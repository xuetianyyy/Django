
**项目目录介绍(Table of Contents)**

[数据库方面](#数据库方面) <br>
[模板方面](#模板方面) <br>
[模型与视图方面](#模型与视图方面)
+ [通用模型类](#1.通用模型类)
+ [用户模块](#2.用户模块)
    + [注册](#注册)
    + [注册](#注册)
    + [激活](#激活)
    + [登录](#登录)
    + [退出](#退出)
    + [个人中心](#个人中心)
    + [个人地址](#个人地址)
+ [商品模块](#3.商品模块)
    + [文件存储](#文件存储)
    + [首页](#首页)
    + [商品详情页](#商品详情页)
    + [商品列表页](#商品列表页)
    + [商品搜索-haystack框架-whoosh引擎](#商品搜索-haystack框架-whoosh引擎)
+ [购物车模块](#购物车模块)
    + [查询](#查询)
    + [增加](#增加)
    + [删除](#删除)
    + [修改](#修改)
+ [订单模块](#订单模块)
    + [提交订单](#提交订单)
    + [确认订单](#确认订单)
    + [订单支付-支付宝](#订单支付-支付宝)
    + [支付查询](#支付查询)
    + [订单评论](#订单评论) <br>
    -
[项目部署方面](#项目部署方面) <br>
[end](#end)
---
# 数据库方面
1. 在项目**static**目录中的(**天天生鲜数据库设计.xmind**)文件中有详细介绍
---
# 模板方面
1. 在项目中使用了四个父模板
    + **bash.html**(主模板)
    
            它作为首页, 详情页, 列表页, 用户注册, 用户登录页的父模板

    + **base_detail_list.html**(继承于bash.html)
    
            它作为商品详情页, 商品列表页的父模板

    + **base_no_cart.html**(继承于bash.html)
    
            它作为购物车, 提交订单, 用户中心三个页面的父模板

    + **base_user_center.html**(继承于base_no_cart.html)
    
            它作为个人信息, 收货地址, 订单详情三个页面的父模板

---
# 模型与视图方面
这是一个基于PC端, 使用Django框架开发的模拟生鲜类B2C网站, 它主要分为以下版块:
## 通用模型类
1. 在**db**模块下定义了一个抽象模型类(BaseModel)其中包括创建时间, 更新时间, 删除标记三个字段, 它用于所有模型继承的父类

----
## 用户模块
### 注册
1. 使用的是自定义用户认证系统**AbstractUser**

2. 在这个模块里有两个模型类(**User**, **Address**)和一个模型管理器类(AddressManage)

         User类, 为自定义的用户认证系统

         Address, 为用户地址

         AddressManage主要实现的目的就是, 方便查询用户有没有默认的收获地址Address继承于AddressManage

3. 用户注册的功能在(**apps.user.views.RegisterViews**)视图类中实现的, 它实现了**get**和**post**两个请求的方法
        其中对于get请求直接返回注册页面

        对于post请求进行注册验证, 其中包括(判断用户是否存在, 以及邮箱激活验证)

        对于用户注册的数据的合法性判断, 这里我使用的是**Vue**在前端注册页面实现的, 我个人认为这样对用户似乎更友好

----
### 激活
1. 对于邮箱激活验证使用到了Django提供的(**send_mail**)模块给用户发送邮件
2. 其次为了避免发送邮件时的任务阻塞, 还使用了(**Celery**)去执行这个任务(在user模块下的task.py文件中定义了任务的发起者)
3. 在发送邮件的过程中还使用了(**itsdangerous**)对用户激活的**URL**进行签名加密

----
### 登录
1. 它在(**apps.user.views.LoginViews**)视图中实现的

2. 另外还为一些未登录不能访问的页面, 使用了Django提供的**LoginRequiredMixin**对类视图进行装饰, 用户判断用户的登录状态

        这里使用到了URL中一个重要的next参数, 来获取用户被拦截之前, 想要访问的路径

        在获取这个参数值的时候, 使用到了get()方法中的默认返回值

        如果next参数是空值, 证明用户之前并没有被拦截过, 此时将get()方法的default参数设置为了首页的重定向跳转

        如果next参数有值, 这意味着用户登录之前被拦截过, 那么登录成功之后, 就跳转到被拦截之前的地址中去

3. 对于登录验证失败的请求, 统一返回登录页面

----
### 退出
1. 它在(**apps.user.views.LoginOutViews**)视图中, 使用系统提供的**logout**方法, 清除用户的登录状态

----
### 个人中心
1. 它的视图定义在(**apps.user.views.UserCenterInfoViews**)中
    
2. 其次个人中心主要分为两个部分
    + 个人信息的展示
    
             主要对联系方式, 及收货地址之类的展示...

    + 用户历史浏览记录的展示, 这里使用的是**redis**作为缓存, 数据类型是**list**
             在用户访问商品详情页面的时候, 在对应的视图(apps.commod.views.DetailViews)将历史浏览记录添加到redis中
             
             在存储记录时, 使用history_前缀+用户的id作为list数据的key
             
             在保存数据时, 储的是商品的id, 并且先判断之前是否存在该商品
                1. 如果存在, 就删除之前的商品的id, 并重新往列表左侧插入记录
                2. 如果不存在, 则直接在列表左侧插入数据
                2. 且商品记录如果大于五条, 则清理列表中最右侧的数据记录
    
    + 在用户访问个人中心页面时, 从**redis**中获取浏览记录, 展示在页面中
    
             先从redis中拿到用户最近浏览的商品**id**

             根据该id再从Mysql商品表中获取到商品的具体数据

             然后对获取到的具体数据, 以redis中的顺序, 进行排序后, 传递给模板

             这样展示给用户浏览记录, 就会和实际的浏览记录顺序保持了一致性
----
### 个人地址
1. 对用户地址的展示, 及添加
    
2. 其中使用到前面自定义的模型管理器类(**apps.user.models.AddressManage**), 来实现对用户是否存在默认收货地址的查询
----
## 商品模块
### 文件存储
1. 由于商品图片存储量比较大, 所以我修改了默认**Django**认的图片存储系统, 重写了**Storage**类的一些方法, 并返回了一个能使用**nginx**访问到图片的完整**URL**地址
    
2. 然后使用了**FastDFS分布式文件存储系统**)作为商品图片的存储服务器
         它解决了海量存储, 容量扩展以及避免文件内容重复等问题
         其次, 结合nginx服务器, 从FastDFS中请求静态资源, 提高了效率问题
    
3. 至于改写**Django**默认文件存储系统的方法, 定义在了(**utils.fdfs.storage**)模块中

         它主要对save方法进行了重写, 其次自定义了url方法的返回值

         在模板中使用时, 需要使用QuerySet.image.url获取url中的返回值得到链接
----
### 首页
1. 它的视图定义在(**apps.commod.views.IndexViews**)中

2. 主要实现首页商品的展示, 以及登陆后现在购物车的数量

3. 在获取数据的时候, 会先尝试着读取**redis**中的缓存

         如果有页面中需要的数据时, 就从缓存中获取数据, 返回给模板

         如果没有页面中需要的数据时, 就从数据库中读取数据, 此时在读取完后设置在缓存中, 并设置有过期时间, 之后将数据返回给模板

3. 其次, 在(**apps.commod.tasks**)模块中还使用了**Celery**创建了一个生成首页静态页面的任务

3. 这个任务在(**apps.commod.admin**)模块中, 我定义了一个触发重新生成首页静态页面机制的基类**BaseModelAdmin**来触发它, 该类用于给涉及到首页数据的模型类继承

4. 那么之后, 只要涉及到首页的数据表被更新时, 就会自动重写静态页面

         这个静态页面, 用户后面给nginx服务器调度的时候使用, 因为nginx处理静态资源的优势

         这样当大量用户请求网站时, 这个静态页面就会派上用场, 因为它不参数后台的交互, 所以在响应客户端的效率上会有明显提升

         其次也能相对的避免网站的DDOS攻击

----
### 商品详情页
1. 对商品信息的获取与展示
2. 设置用户的浏览记录缓存

        在存储记录时, 使用history_前缀+用户的id作为list数据的key

        在保存数据时, 储的是商品的id, 并且先判断之前是否存在该商品
            1. 如果存在, 就删除之前的商品的id, 并重新往列表左侧插入记录
            2. 如果不存在, 则直接在列表左侧插入数据
            2. 且商品记录如果大于五条, 则清理列表中最右侧的数据记录
            
----
### 商品列表页
1. 使用了**django**提供的模板分页功能**Paginator**对商品进行分页展示

----
### 商品搜索-haystack框架-whoosh引擎
1. 在这里主要使用了重要的部分, 搜索引擎(**whoosh**)和全文检索框架(**haystack**)
    + **whoosh**引擎主要对表中建立索引的字段进行关键词分析, 在这里使用了**jieba**工具, 修改该默认的关键词分析功能
    
    **haystack**框架, 主要用于帮助我们使用搜索引擎
    
----
## 购物车模块
### 查询
1. 它的视图定义在(**apps.cart.views.CartViews**)中

2. 主要负责对购物车中商品的展示, 实现如下:

        从redis中获取用户的购物车信息, 得到购物车商品的id和数量

        根据商品的id在商品表中查询到每个商品的具体信息

        根据模板的需求, 在视图中计算一些数据, 并动态的以属性方式添加给商品表查询对象

        然后将商品查询对象, 返回给模板

----
### 增加
1. 它的视图定义在(**apps.cart.views.CartAddViews**)中
2. 在用户点击进入商品详情页面, 或在个人中心历史浏览记录中点击添加购物车时, 添加记录
    + 购物车使用**redis**存储的**hash**类型数据
            其中使用cart_+用户id作为hash的key为每个用户保存一条购物车数据
             
            在存储数据时, 使用商品id作为属性名, 使用添加购物车的商品作为作为属性值, 来存储购物车记录
             
            在存储记录时, 先判断用户是否添加过该商品的记录, 如果没有则添加, 如果有则累加之间的数目

3. 在用户访问购物车页面时, 从**Redis**中获取购物车记录, 展示购物车中的商品

4. 对于前端这一块, 我使用的是**vue-resource**发送ajax请求
        当后台接收到请求时, 对数据进行效验, 然后在redis中添加对应商品的购物车记录
        
----
### 删除
1. 它的视图定义在(**apps.cart.views.CartDelViews**)中

        前端方面也是使用的vue-resource发送ajax请求

        当后台接收到删除请求时, 对数据进行效验, 没问题就删除redis中对应的购物车记录

        然后返回响应个前端, 前端收到正确的响应后, 删除当前商品的DOM节点

---
### 修改
1. 它的视图定义在(**apps.cart.views.CartUpdateViews**)中

2. 由前端发送请求给视图, 视图接收到请求后对数据进行效验, 没问题就更新**redis**中对应的购物车记录

3. 这一块后端做的事比较少, 主要是前端要实现一些功能, 我使用**vue**实现的, 功能如下:

        商品数量增加, 减少, 手动输入, 商品全选, 单选这些事件所需要的方法

        其中对于商品价格的计算, 我在static/js/cart.js中单独封装了一个方法otal_sku_price

        其实商品增加, 减少和文本框手动输入事件的方法, 我将这三个方法集中在一个方法num_add_or_minus里
        
---

## 订单模块
### 提交订单
1. 它的视图定义在(**apps.order.views.OrderPlaceViews**)中

2. 当用户选择好的商品, 点击提交订单时, 在**form**表单中, 提交商品的**id**

3. 当视图接收到用户提交过来的商品**id**时, 对数据进行效验, 然后组织提交订购单模板需要的数据

4. 当模板数据组织好后, 返回给提交订单页面的模板给前端, 并传递单商品的信息给该模板

---
### 确认订单
1. 它的视图定义在(**apps.order.views.OrderCommitViews**)中

2. 当用选择好收获地址, 和支付方式, 并提交订单时, 此时将传递收获地址, 支付方式, 和商品id给确认订单视图

3. 视图接收到数据后, 对数据进行效验, 效验无误后, 需要对相关的数据进行更新

        向订单表中, 添加订单信息

        并对订单中的商品进行遍历, 为每一件不同的商品在订单商品表中, 添加详细的订单商品信息

        遍历的同时更新商品的库存和销量, 商品库存减少, 销量增加

        遍历之后计算出订单中商品的数量和总价格, 并更新到订单表中

        清楚用户购物车中对应的商品记录

4. 在这整个关键的数据库操作中, 为了避免异常发生, 使用了**SQL**事务对整个流程进行管理

        其中在向订单表添加商品之前, 设置了一个事务回滚点

        然后, 为了避免多用户同时购买商品, 而发生商品库存不足, 却卖出超量的产品

        在遍历查询商品详细信息的时候, 设置了一个同步锁(虽然这消耗性能, 且显得没有必要)

        其次如果不用同步锁的话, 那么在结尾向商品表中添加数据之前
            1. 查询商品的销量和库存有没有发生变化, 如果发生了变化, 就进行事务回滚
            2. 然后进行第二次查询, 如果商品库存充足, 就确认这个订单
            3. 如果没有变化, 说明没有人同时购买这个商品, 当然就是一步到位了
            4. 但是这比较麻烦, 由于我时间有限, 在这个案例中只是简单的使用了同步锁, 很抱歉
            5. 其次如果按后面的方法避免用户支付冲突的话, 需要修改Mysql的默认事务隔离机制为可重读

---
### 订单支付-支付宝
1. 它的视图定义在(**apps.order.views.OrderPayViews**)中

2. 这里使用的是第三方接口**python-alipay-sdk**, 支付流程如下

        用户发出支付请求

        视图接收支付请求, 调用支付接口, 并返回支付页面地址

        前端得到支付页面地址, 新开窗口跳转链接, 将用户导向支付页面

        用户在支付页面点击确认支付后, 与此同时, 前端还要发送一个ajax请求, 去查询支付结果

3. 在此进入下一步

---
### 支付查询
1. 它的视图定义在(**apps.order.views.OrderPayQueryViews**)中

2. 当视图接收到支付查询的请求后, 及时调用支付查询接口, 查询支付状态

        如果用户支付成功的话, 需要及时的根据查询到的支付结果, 修改用户的订单状态

        如果支付失败的话, 将跳转到个人订单详情页面中

3. 注意: 在项目中使用的是支付宝沙箱环境

---
### 订单评论
1. 它的视图定义在(**apps.order.views.OrderCommentViews**)中

2. 这里主要实现两个请求的方法
    + **get**请求
            对于get请求, 返回订单评论页面

            并把该模板所需要的相应数据传递过去

    + **post**请求
            该请求用于对于评论的提交, 获取用户提交过来的评论内容

            通过遍历得到, 不同商品的评论信息

            然后将评论信息更新到订单商品表中
            
---
# 项目部署方面
1. 项目使用的是**uwsgi**作为**web**的应用服务器, 用于处理动态的请求

2. 其次使用的是**nginx**作为调度服务器, 它也是最终暴露给用户的服务器, 同时它还处理静态资源

3. 还使用了一个**nginx**作为首页的静态页面服务器

4. 它们之间的协调如下:
    + 当用户访问首页时
    
            调度服务器会将请求转发给静态服务器, 静态服务器返回静态页面给调度服务器,

            调度服务器再将静态页面返回给客户端

    + 当用户访问的是非首页时
    
            调度服务器, 会根据用户请求的地址, 把动态请求分配给uwsgi服务器 

            uwsgi通过application接口将请求发送给Django, Django拿到数据后返回给uwsgi

            uwsgi再返回给调度服务器, 最终调度服务器将资源返回给客户端
            
            如果是静态资源, 调度服务器会直接同静态资源目录中提取出来, 返回给客户端
            
            至于区分静态资源和动态资源, 需要根据自己项目的路由去配置

5. 最终**nginx**还实现了服务的负载均衡, 通过配置多个uwsgi服务器

        将请求轮流转发给不同的uwsgi服务器处理, 这样当请求量比较大的时候, 就会分担了一台服务器的压力

# end
