$(document).ready(function() {
    $("select[name='typeselect']").change(function () {
        //判断是左边还是右边
        var page = 1;
        var classname = $(this).parent().attr('class');

        $(this).next().bind('scroll', function () {
            var scroH = $(this).scrollTop();  //滚动高度
            var viewH = $(this).height();  //可见高度
            var contentH = $(this).children().height(); //内容的高度
            var typeId = $(this).prev().val();
            var classname = $(this).parent().attr('class');
            var that = $(this);
            if (contentH - (scroH + viewH) <= -36.59375){  //距离底部高度小于100px
                 page++;
                 $.post({
                    url: "/cms/typenovel/",
                    data: {typeId: typeId, page: page},
                    success: function (data) {
                        var novel_list = data.result;
                        var ul = that.children();
                        console.dir(ul);
                        if(novel_list.length === 0){
                            ul.append("<li>到底了！！！</li>");
                            that.unbind('scroll')
                        }

                        //动态添加
                        for (var i = 0; i < novel_list.length; i++) {
                            var li = $("<li></li>");
                            if (classname === 'cont left'){
                                li.append('<input type="checkbox" name="novelId" value=' + novel_list[i].novelId + '>');
                            }
                            li.append('<img src="' + novel_list[i].img + '">');
                            li.append('<span>' + novel_list[i].name + '</span>');
                            ul.append(li);
                        }
                        console.log('添加了');

                    }
            })

        }
        });

        if (classname === 'cont left'){
            //获取左边下拉框当前选中的值
            var left_val = $(this).val();
            var selectObj = $("select[name='typeselect']").eq(1);
            var optionObj = selectObj.children("option[value='"+left_val+"']");
            selectObj.children().each(function (i) {
                $(this).removeAttr("disabled");
            });
            optionObj.attr('disabled','disabled');

        }
        //获取改变的分类id
        var typeId = $(this).val();
        var that = $(this);
        $.post({
            url: "/cms/typenovel/",
            data: {typeId: typeId, page: page},
            success: function (data) {
                var novel_list = data.result;

                var ul = that.next().children("ul");
                //动态添加
                ul.empty();
                for (var i = 0; i < novel_list.length; i++) {
                    var li = $("<li></li>");
                    if (classname === 'cont left'){
                        li.append('<input type="checkbox" name="novelId" value=' + novel_list[i].novelId + '>');
                    }
                    li.append('<img src="' + novel_list[i].img + '">');
                    li.append('<span>' + novel_list[i].name + '</span>');
                    ul.append(li);
                }

            }
        })
    });

    $("#submit").click(function () {
        //判断两端下拉框都是选中状态
        var type_select = $("select[name='typeselect']");
        var type_select1 = type_select[0].value;
        var type_select2 = type_select[1].value;
        if (type_select1 === '0' || type_select2 === '0') {
            var tip = $("#tip");
            tip.text("请选择分类");
            tip.css("display", "block");
            setTimeout(function () {
                tip.text("");
                tip.css("display", "none");
            }, 2000);
            return
        }
        var novelsId = new Array();
        //获取当前选中的小说
        $("input[name='novelId']:checked").each(function (i) {
            novelsId.push($(this).val());
            //把当前的li移动到右边
            var li = $(this).parent();
            li.children("input").remove();
            $("#right").prepend(li);
        });
        var novelsId_str = novelsId.join();
        //后台改变小说类别
        $.post({
            url: "/cms/altertype/",
            data: {novelsId: novelsId_str, type: type_select2},
            success: function (data) {

            }
        })

    });


});
