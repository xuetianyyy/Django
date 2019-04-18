var vm = new Vue({
    el: '#order_pay_v',
    data: {

    },
    mounted: function() {
        for (let item of this.$el.children[0].children) {
            if (item.tagName == 'TABLE') {
                node_item = item.children[0].children[0].children[3].children[1]
                if (node_item != undefined) {
                    status = node_item.dataset.status
                    order_id = node_item.dataset.orderId
                    if (status == 4) {
                        node_item.innerText = '去评价';
                        node_item.href = '/order/order_comment/' + order_id;
                    }else if (status == 2){
                        node_item.innerText = '待发货';
                    }else if (status == 3){
                        node_item.innerText = '查看物流';
                    }else if (status == 5){
                        node_item.innerText = '订单已完成';
                    }
                }

            }

        }

    },
    methods: {
        order_pay: function(event) {
            if (event.target.dataset.status == 1) {
                // 订单未支付
                data = {
                    csrfmiddlewaretoken: this.$refs.token.dataset.token,
                    order_id: event.target.dataset.orderId,
                }
                this.$http.post('/order/order_pay', data, {
                    emulateJSON: true
                }).then(result => {
                    if (result.body.res == 3) {
                        // 打开支付页面
                        window.open(result.body.pay_url);
                        // 发送查询交易查询请求
                        this.$http.post('/order/pay_query', data, {
                            emulateJSON: true
                        }).then(result => {
                            if (result.body.res == 100) {
                                console.log('交易状态是:' + result.body.res);
                                // 交易成功
                                alert(result.body.msg)
                                // 刷新页面
                                location.reload()
                            } else {
                                alert(result.body.errmsg);
                            }
                        });
                    } else {
                        alert(result.body.errmsg);
                    }
                })
            } else {
                // 其它情况
            }
        },
    },
})
