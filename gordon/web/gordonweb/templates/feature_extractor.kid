<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">

<link href="/static/js/prettify/prettify.css" type="text/css" rel="stylesheet" />
<script type="text/javascript" src="/static/js/prettify/prettify.js"></script>

<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Feature Extractors</title>
</head>

<body onload="prettyPrint()">

<div class="main_content">        
<h3>Feature Extractor <span py:replace="feature_extractor.id"/>: <span py:replace="feature_extractor.name"/><br/></h3>
<h3>Description:</h3>
<pre>
<span py:replace="feature_extractor.description"/><br/>
</pre>
<h3>Source code:</h3>
<pre class="prettyprint">
<span py:replace="source_code"/>
</pre>

</div>

</body>

</html>
