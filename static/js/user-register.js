window.onload = function(){
  new Vue({
    el: '#user-register',
    data: {
      user_name: '',  // username
      pwd: '',
      cpwd: '',
      email: '',      // 邮箱
      allow: [],      // 协议
      ifallow: false,    // 提醒同意协议
      allow_token: 1,    // 标记注册事件有没有触发
      ifuser: false,     // 判断是否输入
      ifusername: false, // 判断用户是否注册
      ifpwd: false,
      ifcpwd: false,
      ifemail: false,     // 判断邮箱是否为空
      ifemailname: false, // 判断邮箱是否已注册
      error_emiil: false, // 判断邮箱格式是否正确
    },
    methods: {
      submit(){
        // 提交的数据
        this.allow_token = 2;
        let data = {
          csrfmiddlewaretoken: cs_token,
          user_name: this.user_name,
          pwd: this.pwd,
          email: this.email,
          allow: this.allow,
        }
        // 提交审核
        if(this.user_name=='' || this.pwd=='' || this.cpwd=='' || this.email==''){
          alert('请将数据填写完整...')
        }else if(this.pwd !== this.cpwd){
          alert('两次密码输入不同, 请重新输入...')
        }else if(this.emiil()){
          alert('邮箱格式不正确');
        }else if(this.allow[0] == undefined){
          this.ifallow = true;
        }else{
          this.$http.post('/user/register', data, {emulateJSON: true}).then(res => {
            // console.log(res.body.ifuser);
            // console.log(res.body.ifemail);
            // console.log(res.body.iflogin);
            if(res.body.ifuser){
              this.ifusername = true;
              if(res.body.ifemail == false){
                this.ifemailname = false;
              }
            }else if(res.body.ifemail){
              this.ifemailname = true;
              if(res.body.ifuser == false){
                this.ifusername = false;
              }
            }else if(res.body.iflogin){
              alert('注册成功')
              location.href = '/'
            }else{
              this.ifusername = false;
              this.ifemailname = false;
            }
            // console.log(this.ifusername);
            // console.log(this.ifemailname);
          })

        }
      },
      // 判断邮箱格式
      emiil(){
        this.ifemail = true;
        re = /^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$/;
        if(re.test(this.email)){
          this.error_emiil=false;
          return false;
        }else{
          this.error_emiil=true;
          return true;
        }
        // re.test(this.email)?:;
      }
    }, // methods
    created(){

    },
    // 插值表达式更改
    delimiters: [ "[[", "]]" ],
  })
}

