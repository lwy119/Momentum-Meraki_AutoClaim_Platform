$(function(){
    menu_selected(window.location.pathname);

    $(".viewbtn").on("click", function(){
        $(this).parent().parent().next(".fold").toggleClass("hidden");
    });

    $(".confirm-org").on("click", function(){
        var this_obj = $(this);
        this_obj.hide();
        this_obj.siblings(".loading-dots").removeClass("hidden");
        this_obj.siblings(".loading-dots").addClass("inline");
        var store_number = this_obj.parent().parent().siblings(".store-number").html();
        var store_name = this_obj.parent().parent().siblings(".store-name").html();
        var order_number = this_obj.parent().parent().siblings(".order-number").html();
        var org_id = this_obj.siblings("select").val();
        var org_name = this_obj.siblings("select").children(":selected").text();
        var data = {
            'store_number': store_number,
            'store_name': store_name,
            'order_number': order_number,
            'org_id': org_id,
            'org_name': org_name
        }

        $.ajax({
            type: 'POST',
            url: '/corporate/register/confirm_org',
            data: {
                'data': JSON.stringify(data)
            },
            success: function(res){
                this_obj.siblings(".loading-dots").addClass("hidden");
                this_obj.siblings(".loading-dots").removeClass("inline");
                if(res.includes("</div>")){
                    res_html = res.split("split");
                    this_obj.parent().parent().parent().find(".viewbtn").removeClass("hidden");
                    this_obj.parent().parent().parent().next().find(".row").html(res_html[0]);
                    this_obj.parent().parent().siblings(".device-count").html(res_html[1]);
                    this_obj.parent().parent().siblings(".config-template").find(".select").removeClass("hidden");
                    this_obj.parent().parent().siblings(".config-template").find("select").append(res_html[2]);
                    this_obj.prev().remove();
                    this_obj.parent().prepend(`<span>${org_name}</span>`);
                    this_obj.siblings(".text-success").show();
                }else{
                    this_obj.show();
                    this_obj.parent().parent().parent().find(".viewbtn").removeClass("hidden");
                    this_obj.parent().parent().parent().next().find(".row").append(`<div class="row-msg small-margin-left">${res}</div>`);
                }
            }
        });
    });

    $(".confirm-template").on("click", function(){
        var this_obj = $(this);
        this_obj.hide();
        this_obj.siblings(".loading-dots").removeClass("hidden");
        this_obj.siblings(".loading-dots").addClass("inline");
        var store_number = this_obj.parent().parent().siblings(".store-number").html();
        var template_id = this_obj.siblings("select").val();
        var template_name = this_obj.siblings("select").children(":selected").text();
        var data = {
            'store_number': store_number,
            'template_id': template_id,
            'template_name': template_name
        }

        $.ajax({
            type: 'POST',
            url: '/corporate/register/confirm_template',
            data: {
                'data': JSON.stringify(data)
            },
            success: function(res){
                this_obj.siblings(".loading-dots").addClass("hidden");
                this_obj.siblings(".loading-dots").removeClass("inline");
                if(res == "Y"){
                    this_obj.prev().remove();
                    this_obj.parent().prepend(`<span>${template_name}</span>`);
                    this_obj.siblings(".text-success").show();
                }else{
                    this_obj.show();
                    this_obj.parent().parent().parent().next().find(".row").append(`<div class="row-msg small-margin-left">${res}</div>`);
                }
            }
        });
    });

    $(".confirm-modify").on("click", function(){
        var this_obj = $(this);
        var old_store_number = this_obj.parent().siblings(".old-store-number").html();
        var old_store_name = this_obj.parent().siblings(".old-store-name").html();
        var new_store_number = this_obj.parent().siblings(".new-store-number").find("input").val();
        var new_store_name = this_obj.parent().siblings(".new-store-name").find("input").val();
        if(new_store_number != "" && new_store_number != old_store_number || new_store_name != "" && new_store_name != old_store_name){
            this_obj.hide();
            this_obj.siblings(".loading-dots").removeClass("hidden");
            this_obj.siblings(".loading-dots").addClass("inline");
            var data = {
                'old_store_number': old_store_number,
                'old_store_name': old_store_name,
                'new_store_number': new_store_number,
                'new_store_name': new_store_name
            }
            $.ajax({
                type: 'POST',
                url: '/corporate/modify',
                data: {
                    'data': JSON.stringify(data)
                },
                success: function(res){
                    console.log(res);
                    this_obj.show();
                    this_obj.siblings(".loading-dots").addClass("hidden");
                    this_obj.siblings(".loading-dots").removeClass("inline");
                    if(res == "None"){
                        if(new_store_number != "" && new_store_number != old_store_number){
                            this_obj.parent().siblings(".new-store-number").find(".text-success").hide();
                            this_obj.parent().siblings(".new-store-number").find(".text-danger").show();
                        }
                        if(new_store_name != "" && new_store_name != old_store_name){
                            this_obj.parent().siblings(".new-store-name").find(".text-success").hide();
                            this_obj.parent().siblings(".new-store-name").find(".text-danger").show();
                        }
                        this_obj.parent().siblings(".new-store-number").find("input").val("");
                        this_obj.parent().siblings(".new-store-name").find("input").val("");
                    }else{
                        if(res == "Number"){
                            this_obj.parent().siblings(".new-store-number").find(".text-success").show();
                            this_obj.parent().siblings(".new-store-number").find(".text-danger").hide();
                            if(new_store_name != "" && new_store_name != old_store_name){
                                this_obj.parent().siblings(".new-store-name").find(".text-success").hide();
                                this_obj.parent().siblings(".new-store-name").find(".text-danger").show();
                            }
                            this_obj.parent().siblings(".old-store-number").html(new_store_number);
                        }else if(res == "Name"){
                            if(new_store_number != "" && new_store_number != old_store_number){
                                this_obj.parent().siblings(".new-store-number").find(".text-success").hide();
                                this_obj.parent().siblings(".new-store-number").find(".text-danger").show();
                            }
                            this_obj.parent().siblings(".new-store-name").find(".text-success").show();
                            this_obj.parent().siblings(".new-store-name").find(".text-danger").hide();
                            this_obj.parent().siblings(".old-store-name").html(new_store_name);
                        }else if(res == "Both"){
                            this_obj.parent().siblings(".new-store-number").find(".text-success").show();
                            this_obj.parent().siblings(".new-store-number").find(".text-danger").hide();
                            this_obj.parent().siblings(".new-store-name").find(".text-success").show();
                            this_obj.parent().siblings(".new-store-name").find(".text-danger").hide();
                            this_obj.parent().siblings(".old-store-number").html(new_store_number);
                            this_obj.parent().siblings(".old-store-name").html(new_store_name);
                        }
                        this_obj.parent().siblings(".new-store-number").find("input").val("");
                        this_obj.parent().siblings(".new-store-name").find("input").val("");
                    }
                }
            });
        }
    });
});

function menu_selected(pathname){
    if(pathname == "/corporate/register"){
        $('#menu_corporate_register').addClass("selected");
    }else if(pathname == "/corporate/modify"){
        $('#menu_corporate_modify').addClass("selected");
    }else if(pathname == "/corporate/history"){
        $('#menu_corporate_history').addClass("selected");
    }
}
