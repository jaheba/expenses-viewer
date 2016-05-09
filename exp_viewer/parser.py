import re
import sys
import datetime
from decimal import Decimal
from StringIO import StringIO
# import exp_db as db

from lxml import etree

CURRENCIES = set([
    "aed", "afn", "all", "amd", "ang", "aoa", "ars", "aud",
    "awg", "azn", "bam", "bbd", "bdt", "bgn", "bhd", "bif", "bmd", "bnd", "bob",
    "brl", "bsd", "btn", "bwp", "byr", "bzd", "cad", "cdf", "chf", "clp", "cny",
    "cop", "crc", "cuc", "cup", "cve", "czk", "djf", "dkk", "dop", "dzd", "egp",
    "ern", "etb", "eur", "fjd", "fkp", "gbp", "gel", "ggp", "ghs", "gip", "gmd",
    "gnf", "gtq", "gyd", "hkd", "hnl", "hrk", "htg", "huf", "idr", "ils", "imp",
    "inr", "iqd", "irr", "isk", "jep", "jmd", "jod", "jpy", "kes", "kgs", "khr",
    "kmf", "kpw", "krw", "kwd", "kyd", "kzt", "lak", "lbp", "lkr", "lrd", "lsl",
    "ltl", "lvl", "lyd", "mad", "mdl", "mga", "mkd", "mmk", "mnt", "mop", "mro",
    "mur", "mvr", "mwk", "mxn", "myr", "mzn", "nad", "ngn", "nio", "nok", "npr",
    "nzd", "omr", "pab", "pen", "pgk", "php", "pkr", "pln", "pyg", "qar", "ron",
    "rsd", "rub", "rwf", "sar", "sbd", "scr", "sdg", "sek", "sgd", "shp", "sll",
    "sos", "srd", "std", "svc", "syp", "szl", "thb", "tjs", "tmt", "tnd", "top",
    "try", "ttd", "tvd", "twd", "tzs", "uah", "ugx", "usd", "uyu", "uzs", "vef",
    "vnd", "vuv", "wst", "xaf", "xcd", "xdr", "xof", "xpf", "yer", "zar", "zmw",
    "zwd"
])

status_types = set(["notsubmitted", "submitted", "reimbursed", "accounted"])

expense_types = set(["accom", "equipment", "food", "misc", "travel"])

item_requirements = {
    'accom': 'name',
    'food': 'shop',
    'travel': 'journey',
}

paiby_other = set(['other', 'purchaseorder'])


class ParseError(Exception):
    def __init__(self, message, node):
        Exception.__init__(self, message)
        self.message = message
        self.node = node


class Budget(object):
    @classmethod
    def from_node(cls, node):
        return cls(
            name=node.get('id'),
            descr=node.text,
            initial=Decimal(node.get('initial')),
            active=node.get('active') == 'true'
        )

    def __init__(self, name, descr, initial, active):
        self.name = name
        self.descr = descr
        self.initial = initial
        self.balance_on_file = initial
        self.balance = initial
        self.active = active

    def __repr__(self):
        return '<Budget:{name} (B:{balance}, S:{file})>'.format(
            name=self.name, balance=self.balance, file=self.balance_on_file)


class Person(object):
    @classmethod
    def from_node(cls, node):
        return cls(node.get('id'), node.get('name'))

    def __init__(self, id, name):
        self.id = id
        self.name = name


class Expense(object):
    @classmethod
    def from_node(cls, node, env):
        expenses = [ExpenseItem.from_node(child, env)
                    for child in node.xpath('*[not(self::descr)]')]

        return cls(node.xpath('descr')[0].text, expenses)

    def __init__(self, text, expenses):
        self.text = text
        self.expenses = expenses

    def sum(self):
        return sum(exp.gbp for exp in self.expenses)

    def has_unaccounted(self):
        return any(exp.status != 'accounted' for exp in self.expenses)

    def to_json(self, index):
        return {
            "description": self.text,
            "expenses": [exp.to_json(i) for i, exp in enumerate(self.expenses)],
            "sum": '%.2f' %self.sum(),
            "status": 'TODO',
            "idx": index
        }


def check(node, condition, message):
    if not condition:
        raise ParseError(message, node)

class ExpenseItem(object):
    @classmethod
    def from_node(cls, node, env):
        budgetid = node.get('budgetid')
        status = node.get('status')
        paidby = node.get('paidby')
        date = node.get('date')
        gbp = node.get('gbp')

        check(node, node.tag in expense_types, 'Unknown expense tag %s' % node.tag)
        check(node, budgetid in env.budgets, 'Unknown budget ID %s.' % budgetid)
        check(node, status in status_types, 'Unknown status %s.' % status)
        check(node, date, 'Required attribute date missing')
        check(node, gbp, 'Required attribute gbp missing')
        check(node, paidby in paiby_other or paidby in env.people, 'Unknown person ' + paidby)

        try:
            gbp = Decimal(gbp)
        except TypeError:
            raise ParseError(node, 'Invalid value for gbp `%s`' %gbp)

        budget = env.budgets[budgetid]

        # different items require different fields
        if node.tag in item_requirements:
            text = node.get(item_requirements[node.tag])
            assert text, 'Required attribute %s' % (item_requirements[node.tag])
        else:
            text = node.text.strip()

        for_ = node.get('for', '')
        if not for_ and paidby not in ('other', 'purchaseorder'):
            assert paidby != 'gpc', 'Who paid for %s %s' % (node.tag, node.text)
            for_ = env.people[paidby].name

        if paidby in env.people:
            paidby = env.people[paidby].name
        # assert any(contains(node.attrib, cur) for cur in CURRENCIES), (
            # 'Element %s %s has no currency.'
        # )

        return cls(node.tag, text, for_, date, gbp, paidby, budget, status)

    def to_json(self, index):
        return {
            "status": self.status[0].upper(),
            "type": self.type.upper()[:6],
            "gbp": str(self.gbp),
            "date": self.date,
            "paidby": self.paidby,
            "for": self.for_,
            "description": self.text,
            "idx": index
        }

    def __init__(self, type, text, for_, date, gbp, paidby, budget, status):
        self.type = type
        self.text = text
        self.for_ = for_
        self.date = date
        self.gbp = gbp
        self.paidby = paidby
        self.budget = budget
        self.status = status

    def end_date(self):
        if "/" in self.date:
            date = self.date.partition("/")[2]
        else:
            date = self.date
        return datetime.date(*[int(x) for x in date.split("-")])

    def __str__(self):
        formatters = {
            'accom': lambda t, f: 'Accomodation (%s) (%s)' % (t, f),
            'food': lambda t, f: 'Food (%s) (%s)' % (t, f),
            'travel': lambda t, f: 'Travel (%s) (%s)' % (t, f),
            'equipment': lambda t, f: t + '(%s)' % f if f else ''
        }
        default = lambda t, f: '%s %s' % (t, f)
        format_ = formatters.get(self.type, default)
        return format_(self.text.strip(), self.for_)


class Expenses(object):

    def __init__(self, root):
        self.people = {node.get('id'): Person.from_node(node)
                       for node in root.xpath('person')}

        self.budgets = {node.get('id'): Budget.from_node(node)
                        for node in root.xpath('budget')}

        self.expenses = [Expense.from_node(node, self)
                         for node in root.xpath('expense')]

    def calculate_budgets(self):
        accounts = {}

        for expense in self.expenses:
            for item in expense.expenses:
                account = accounts.get((item.budget, item.status))
                if account is None:
                    account = CreditDebit(item.budget, 0, item.status)
                    accounts[(item.budget, item.status)] = account

                account.amount += item.gbp
                item.budget.balance -= item.gbp
                if item.status == 'accounted':
                    item.budget.balance_on_file -= item.gbp


class CreditDebit(object):
    def __init__(self, budget, amount, status):
        self.budget = budget
        self.amount = amount
        self.status = status


def analyse(tree):
    root = tree.getroot()
    exp = Expenses(root)
    # exp.calculate_budgets()
    # pprint(exp.budgets)
    # for expenses in exp.expenses:
        # for item in expenses.expenses:
            # db.insert(db.con, item)
        # db.insert(db.con, exp.budgets.values()[0])
    # print exp.expenses[0].to_json()
    return exp

def parse(path):
    with open(path) as xml_file:
        parser = etree.XMLParser(remove_comments=False)
        tree = etree.parse(xml_file, parser=parser)
        exp = analyse(tree)
        return exp


preamble_re = re.compile(r'^(.+)(?=<expenses>)', flags=re.MULTILINE+re.S)

def fix_preamble(xml, preamble):
    return preamble_re.sub(preamble, xml, 1)

def get_preamble(text):
    return preamble_re.search(text).group(0)

def get_xml(path):
    with open(path) as xml_file:
        xml = xml_file.read()
        parser = etree.XMLParser(remove_comments=False)
        tree = etree.parse(StringIO(xml), parser=parser)
    return xml, tree

def set_status(path, changes, status):
    xml, tree = get_xml(path)
    expenses = tree.xpath('expense')

    for exp, item in changes:
        expenses[exp][item+1].set('status', status)

    new = etree.tostring(tree)
    with open(path, 'w') as xml_file:
        xml_file.write(fix_preamble(new, get_preamble(xml)))


def main(path):
    try:
        with open(path) as xml_file:
            parser = etree.XMLParser(remove_comments=False)
            tree = etree.parse(xml_file, parser=parser)
            exp = analyse(tree)
            print exp
    except AssertionError as e:
        print >> sys.stderr, e
        sys.exit(1)

if __name__ == '__main__':
    main('expenses.xml')