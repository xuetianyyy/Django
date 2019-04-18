// 这里的sku_name对应的是商品sku_id
var vm = new Vue({
    el: '#vue-dom',
    data: {
        checked: false,
        checkedNames: [],
        checkedArr: [],
        del_ul_obj: {},
    },
    mounted: function(){
        // 获取所有商品名称列表
        this.checkedArr = JSON.parse(this.$refs.sku_ids.innerText);
    },
    methods: {
        // 保留精确小数点
        formatDecimal: function(num, decimal) {
            num = num.toString()
            let index = num.indexOf('.')
            if (index !== -1) {
                num = num.substring(0, decimal + index + 1)
            } else {
                num = num.substring(0)
            }
            return parseFloat(num).toFixed(decimal)
        },

        // 封装一个统计单个商品价钱小计的方法
        count_sku_price: function(sku_name) {
            // 如果个节点存在
            if (this.$refs[sku_name + '-ul'] != undefined) {
                // 商品单价
                price_str = this.$refs[sku_name + '-ul'].children[4].innerText // 得到DOM字符串
                price = parseFloat(price_str.substring(0, price_str.length - 1));
                // 商品数量
                sku_nums = parseInt(this.$refs[sku_name + '-ul'].children[5].children[0].children[1].value);
                // 单个商品价钱小计
                count_price = parseFloat(price * sku_nums);
                // 重新定义商品小计的HTML
                this.$refs[sku_name + '-ul'].children[6].innerText = this.formatDecimal(count_price, 2) + '元';
                // 返回单个商品的数量, 和单个商品小计的价钱
                return [sku_nums, count_price]
            }
        },

        // 计算被选中购买的商品价格方法
        total_sku_price: function() {
            total_price = 0; // 存储总商品价格
            sku_count_all = 0; // 存储所有商品的数量
            total_count = 0; // 存储选中购买商品的总数量
            // 遍历已经被选中的元素
            for (let sku_name1 of this.checkedArr) {
                // 如果商品不存在, 就删除总列表中的商品名称
                if (this.$refs[sku_name1 + '-ul'] === undefined) {
                    delete this.checkedArr[this.checkedArr.indexOf(sku_name1)]
                } else {
                    // 得到购物车中所有商品的数量, 单个商品小计DOM树节点
                    sku_count_all += parseInt(this.$refs[sku_name1 + '-ul'].children[5].children[0].children[1].value);

                    if (this.checkedNames.length == 0) {
                        this.count_sku_price(sku_name1);
                    } else {
                        for (let sku_name2 of this.checkedNames) {
                            if (sku_name1 == sku_name2) {
                                // 调用上面封装的方法
                                let [sku_nums, count_price] = this.count_sku_price(sku_name2);
                                // console.log(sku_nums);
                                // console.log(count_price);
                                // 已经购买的商品总价
                                total_price += count_price;
                                // 已经购买的商品数量
                                total_count += sku_nums;
                            } else {
                                // 如果数据有改变, 重新定义商品小计的价钱
                                this.count_sku_price(sku_name1);
                            }
                        }
                    }
                }
            }
            // 全部商品总件数
            this.$refs.sku_count_all.innerHTML = sku_count_all;
            // 已购买商品总价
            this.$refs.total_price.innerHTML = this.formatDecimal(total_price, 2);
            // 已购买商品件数
            this.$refs.total_skus.innerHTML = total_count;
        },

        // 商品数量添加, 减少, 输入通用事件, 并发送ajax请求更新购物车记录
        num_add_or_minus: function(event) {
            // 获取自定义属性, 拼接出ref属性值, 并获取商品数量
            sku_name = event.target.dataset.alter;
            sku_count_name = sku_name + '-count';
            sku_count = parseInt(this.$refs[sku_count_name].value); // 备份当前数量
            if (event.target.className == 'add fl') {
                // 商品数量增加
                sku_count += 1;
            } else if (event.target.className == 'minus fl') {
                // 商品数量减少
                sku_count -= 1;
                if (sku_count < 1) {
                    sku_count = 1;
                    return // 非法数据退出函数
                }
            } else if (event.target.className == 'num_show fl') {
                // 商品数量手动输入
                if (event.target.value == ' ') {
                    event.target.value = 1;
                    return // 非法数据退出函数
                } else if (isNaN(parseInt(event.target.value))) {
                    event.target.value = 1;
                    return // 非法数据退出函数
                }
            }

            // 发送后端请求更新购物车记录
            data = {
                csrfmiddlewaretoken: this.$refs.sku_ids.dataset.token,
                sku_id: this.$refs[sku_name + '-id'].dataset.skuId,
                sku_count: this.$refs[sku_name + '-count'].value,
            }
            this.$http.post('/cart/cart_update', data, {
                emulateJSON: true
            }).then(function(result) {
                if (result.body.res != 5) {
                    // 更新失败
                    alert(result.body.errmsg)
                } else {
                    // 更新成功
                    if (event.target.className != 'num_show fl') {
                        // 重新设置商品数量
                        this.$refs[sku_name + '-count'].value = sku_count;
                    }
                    this.total_sku_price() // 调用商品总价统计, 且更新商品价钱小计
                }
            })
        },

        // 购物车删除记录事件
        sku_cart_del: function(event) {
            // 获取商品的id
            sku_name = event.target.dataset.skuDel;
            sku_id = this.$refs[sku_name + '-id'].dataset.skuId;
            // 请求体
            data = {
                csrfmiddlewaretoken: this.$refs.sku_ids.dataset.token,
                sku_id: sku_id,
            }
            // 发送请求
            this.$http.post('/cart/cart_del', data, {
                emulateJSON: true
            }).then(function(result) {
                if (result.body.res == 2) {
                    // 删除成功
                    sku_name = event.target.dataset.skuDel;
                    ul_node = this.$refs[sku_name + '-ul']; // 获取当前的ul节点
                    ul_node.parentNode.removeChild(ul_node);
                    delete this.checkedNames[this.checkedNames.indexOf(sku_name)]; // 删除DOM文档
                    delete this.$refs[sku_name + '-ul']; // 删除vue的节点
                    this.total_sku_price();
                } else {
                    alert('商品删除失败, ' + result.body.errmsg)
                }
            })
        },

        // 控制全选与反选事件
        check_all: function() {
            if (this.checked) {
                this.checkedNames = this.checkedArr
            } else {
                this.checkedNames = []
            }
            // console.log(this.checkedArr);
            // console.log(this.checkedNames);
            this.total_sku_price();
        },
    },
    watch: {
        "checkedNames": function() {
            if (this.checkedNames.length == this.checkedArr.length) {
                this.checked = true
            } else {
                this.checked = false
            }
        }
    }
});
