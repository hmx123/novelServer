$("#typespider").click(function () {
    //获取小说分类id
    var typeId = $("select[name='noveltype']").val();
    if (typeId === "0") {
        var type_msg = $("#type_msg");
        type_msg.text("请选择小说分类!");
        setTimeout(function () {
            type_msg.text("");
        }, 1000);
        return
    }
    //获取页码 限制
    var page = $("input[name='page']");
    if (isNumber(page.val()) === false) {
        var page_msg = $("#page_msg");
        page_msg.text("请输入int类型!");
        setTimeout(function () {
            page_msg.text("");
            page.val(null);
        }, 1000);
        return
    }
    var limit = $("input[name='limit']");
    if (isNumber(limit.val()) === false) {
        var limit_msg = $("#limit_msg");
        limit_msg.text("请输入int类型!");
        setTimeout(function () {
            limit_msg.text("");
            limit.val(null);
        }, 1000);
        return
    }
    var tip = $("#tip");
    $.post({
        url: "/cms/ftypespider/",
        data: {page: page.val(), limit: limit.val(), typeId: typeId},
        success: function (data) {
            tip.text(data.msg);
            tip.css("display", "block");
            setTimeout(function () {
            tip.text("");
            tip.css("display", "none");
        }, 2000);
        },
    });
});

function isNumber(value) {         //验证是否为数字
    var patrn = /^(-)?\d+(\.\d+)?$/;
    if (patrn.exec(value) == null || value == "") {
        return false
    } else {
        return true
    }
}

$("#namespider").click(function () {
    //获取搜索名字
    var novelname = $("input[name='novelname']");
    var tip = $("#tip");
    $.post({
        url: "/cms/fsearchspider/",
        data: {keyword: novelname.val()},
        success: function (data) {
            tip.text(data.msg);
            tip.css("display", "block");
            setTimeout(function () {
            tip.text("");
            tip.css("display", "none");
        }, 2000);
        },
    });

});




