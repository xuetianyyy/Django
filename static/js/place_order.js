var vm = new Vue({
    el: '#place_order',
    data: {
        user_addr: '', // 绑定收货地址单选框
        alipay_way: '3', // 绑定收货地址单选框
        sku_ids: [], // 存储商品的sku_id列表
        popup: false, // 订单提交成功弹窗显示
    },
    mounted: function() {
        // 设置收货地址为默认地址
        this.user_addr = this.$refs.default_addr.dataset.dfaddr;
        // 获取所有商品id
        for (let item of this.$refs.skus.children) {
            this.sku_ids.push(item.dataset.skuId)
        }
        // console.log(this.user_addr);
        // console.log(this.alipay_way);
        // console.log(this.sku_ids);
        // console.log(this.user_addr);
    },
    methods: {
        // 提交支付订单
        order_commit: function() {
            data = {
                csrfmiddlewaretoken: this.$refs.skus.dataset.token,
                addr_id: this.user_addr,
                pay_way: this.alipay_way,
                sku_ids: this.sku_ids,
            }
            this.$http.post('/order/commit', data, {emulateJSON: true}).then(result => {
                console.log(result.body);
                if(result.body.res == 6){
                    // alert(result.body.msg)
                    this.popup = true;
                    setTimeout(function(){
                        window.location.href = '/user/user_center_order/1';
                    },2000)
                }else{
                    alert(result.body.errmsg)
                }
            })
    },
    },
    delimiters: ["[[", "]]"],
})
