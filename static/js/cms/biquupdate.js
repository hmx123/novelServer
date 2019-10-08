 $(function () {
            $("#j_cbAll").click(function () {
                var cked=$(this).prop("checked");//保存当前复选框的选中状态
                //获取tbody中所有的复选框
                $("#DataTables_Table_0").find(":checkbox").prop("checked",cked);
            });

            //获取tbody中所有的复选框
            $("#DataTables_Table_0").find(":checkbox").click(function () {
                var length1=$("#DataTables_Table_0").find(":checkbox").length;
                var length2=$("#DataTables_Table_0").find(":checked").length;
                //二者比较,如果相同,让最上面的复选框选中,否则不选中
                if(length1==length2){
                    //都选中了
                    $("#j_cbAll").prop("checked",true);
                }else{
                    //有没选中
                    $("#j_cbAll").prop("checked",false);
                }
            });
        });
