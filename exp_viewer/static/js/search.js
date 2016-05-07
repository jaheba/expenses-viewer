

var hide_all = function() {
    $(".card").hide();
}

var search_for = function(query, field, cards, fuzzy) {
    var comp;
    if (field == "gbp") {
        comp = function(other){
            return Math.abs(query - parseFloat(other)) <= fuzzy
        };
    } else {
        var q = query.toUpperCase();
        comp = function(other){
            return other.toUpperCase().includes(q);
        }
    }

    return _.filter(cards, function(card){
        var tds = $("td." + field, card);
        return _.some(_.map(tds, function(td){

            if (comp(td.textContent)) {
                return true;
            }
            $(td.parentElement).addClass("deselected");
        }));
    });
}
let progressbar = $("#progress");


var filter_boxes = function(status, cards) {
    let size = $("td.status").length;
    let count = 0;

    return _.filter(cards, function(card){
        return _.some(_.map($("td.status", card), function(td){

            if (status.includes(td.textContent)) {
                return true
            }
            $(td.parentElement).addClass("deselected");
        }));
    });
}


$(function (){
    var cards = cards = $(".card");

    var reset = function() {
        $("tr").removeClass("deselected");
        cards = $(".card");
        cards.hide();

        cb_handler(null, true);
        filter_searches();
        gbp_handler(null, true);
        cards.show();
    }

    var filter_searches = function() {
        _.each(["type", "paidby", "for", "description"], function(field) {
            let query = $("#" + field).val();
            if (query){
                cards = search_for(query, field, cards);
            }
        });
    }

    var handler = function(e, dry){
        let old_val = $(e.target).data('old') || "";
        let new_val = e.target.value;


        if (cards == undefined || old_val.length > new_val.length) {
            cards = $(".card");
            $("tr").removeClass("deselected");
            filter_searches();
            gbp_handler(null, true);
            cb_handler(null, true);
        } else if (old_val.length == new_val.length) {
            return;
        }

        $(e.target).data('old', new_val);

        cards.hide();

        cards = $(search_for(new_val, e.target.id, cards));
        cards.show();
    };

    let gbp = $("#gbp");
    var gbp_handler = function(e, dry){
        if(!dry) {
            cards = $(".card");
            $("tr").removeClass("deselected");
            cards.hide();

            cb_handler(null, true);
            filter_searches();
        }
        let amount = parseFloat(gbp.val());
        let fuzzy = $("#fuzzy").is(":checked")? 0.1 : 0;

        if(amount){
            cards = $(search_for(amount, "gbp", cards, Math.max(fuzzy?1:0, amount*fuzzy)));
        }
        if(!dry) {cards.show();}
    }

    let cb_handler = function(e, dry) {
        if (e && $(e.target).is(":checked")) {
            cards = $(".card");
            $("tr").removeClass("deselected");
            filter_searches();
            gbp_handler(null, true);
            cards = $(cards);
        }

        let status = "";
        if ($("#notsubmitted").is(":checked")){
            status += "N"
        }
        if ($("#submitted").is(":checked")){
            status += "S"
        }
        if ($("#reimbursed").is(":checked")){
            status += "R"
        }
        if ($("#accounted").is(":checked")){
            status += "A"
        }
        if(!dry) {cards.hide();}
        cards = $(filter_boxes(status, cards));
        if(!dry) {cards.show();}
    };

    if($("#submit-flag").data("flag")) {
        $("#notsubmitted").prop("checked", true).parent().hide();
        $("#submitted").prop("checked", false).parent().hide();
        $("#reimbursed").prop("checked", false).parent().hide();
        $("#accounted").prop("checked", false).parent().hide();

        // $("tr.N td.type").html('<strong><a href="#">ACCEPT</a></strong>');
        $("tr.N").addClass("ready");
        $("table").on("click", "tr.N", function(e){
            $(this).removeClass("N").addClass("S").addClass("dirty");
            return false;
        });

        $("#save-btn").show().click(function(){
            $(this).addClass("is-loading");
            let submitted = _.map($(".dirty"), function(self){
                let $self = $(self);
                return [$self.closest(".card").data('index'), $self.data('index')];
            });

            $.ajax({
                type: "POST",
                url: "/submit",
                data: JSON.stringify(submitted),
                contentType: "application/json; charset=utf-8",
                // dataType: "json"
            }).done(function(data){
                window.location.reload()

                $("#save-btn").removeClass("is-loading");
            });
        })

        $(document).on("click", ".dirty", function(e){
            $(this).removeClass("S").addClass("N").removeClass("dirty");
        });
    }

    $("#type").on("keyup", handler);
    $("#paidby").on("keyup", handler);
    $("#for").on("keyup", handler);
    $("#description").on("keyup", handler);
    $("#gbp").on("change", gbp_handler);

    $("#notsubmitted").change(cb_handler);
    $("#submitted").change(cb_handler);
    $("#reimbursed").change(cb_handler);
    $("#accounted").change(cb_handler);

    $("#fuzzy").change(reset);

    window.reset = reset;
    reset();
    $("#expenses").show();
});

