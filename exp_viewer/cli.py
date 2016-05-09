

import os
import click
from parser import parse, ParseError
import decimal
from lxml import etree

@click.group()
def cli():
    pass

@cli.command()
@click.argument('expenses', envvar='SOFTDEV_EXPENSES', type=click.Path(exists=True))
def verify(expenses):
    try:
        parse(expenses)
    except etree.XMLSyntaxError as e:
        error = click.style("lxml SyntaxError:", bold=True, fg='red')
        click.echo(error + ' ' + str(e))
    except ParseError as e:
        error = click.style("Error:", bold=True, fg='red')
        click.echo(' '.join([error, e.message]))
        click.echo('  ' + etree.tostring(e.node))
    except decimal.InvalidOperation as e:
        error = click.style("Error:", bold=True, fg='red')
        click.echo(' '.join([error, e.message]))


@cli.command()
@click.argument('expenses', envvar='SOFTDEV_EXPENSES', type=click.Path(exists=True))
def serve(expenses):
    import app
    app.make_app(expenses)
    app.run(debug=False)


@cli.command()
@click.argument('expenses', envvar='SOFTDEV_EXPENSES', type=click.Path(exists=True))
@click.option('--out', '-o', type=click.Path(), required=True)
def freeze(expenses, out):
    from freeze import freeze
    freeze(expenses, os.path.abspath(out))

if __name__ == '__main__':
    cli()