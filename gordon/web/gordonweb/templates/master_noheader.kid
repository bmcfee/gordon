<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import sitetemplate ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="sitetemplate">

<head py:match="item.tag=='{http://www.w3.org/1999/xhtml}head'" py:attrs="item.items()">
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title py:replace="''">Your title goes here</title>
    <meta py:replace="item[:]"/>
    <style type="text/css">
        #pageLogin
        {
            font-size: 10px;
            font-family: verdana;
            text-align: right;
        }
    </style>
    <style type="text/css" media="screen">
@import "${tg.url('/static/css/style.css')}";
</style>
</head>

<body py:match="item.tag=='{http://www.w3.org/1999/xhtml}body'" py:attrs="item.items()">
    <div py:if="tg.config('identity.on') and not defined('logging_in')" id="pageLogin">
        <span py:if="tg.identity.anonymous">
            <a href="${tg.url('/login')}">Login</a>
        </span>
        <span py:if="not tg.identity.anonymous">
            Welcome ${tg.identity.user.display_name}.
            <a href="${tg.url('/logout')}">Logout</a>
        </span>
    </div>

    <div id="sidebar_padded">
    <a href="/">Gordon Home</a><br/>
    <hr/>
    <a href="/artists">Browse Artists</a><br/>
    <a href="/albums">Browse Albums</a><br/>
    <a href="/tracks">Browse Tracks</a><br/>	
    <hr/>		     
    <a href="/admin">Administration</a><br/>
    <a href="/stats">View Statistics</a><br/>
    <a href="/artists_all">All Artists (slow)</a><br/>
    <a href="/albums_all">All Albums (slow)</a><br/>
        <hr/>
    <form action="/query" method="post">
    <label for="artist" >Artist:</label>
    <input name="artist" type="text" size="10"/><br/>
    <label for="album" >Album:</label>
    <input name="album" type="text" size="10"/><br/>
    <label for="track" >Track:</label>
    <input name="track" type="text" size="10"/><br/>
    <input type="submit" value="Search"/><br/>
    </form>
    </div>
 

    <div id="main_content">
    <div id="status_block" class="flash" py:if="value_of('tg_flash', None)" py:content="tg_flash"></div>
    <div py:replace="[item.text]+item[:]"/>
    <!-- End of main_content -->
    </div>
<div id="footer"> Copyright &copy; 2010 Gordon Development Team
</div>
</body>

</html>
