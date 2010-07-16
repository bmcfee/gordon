<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Track <span py:replace="track.id"/></title>

<script type="text/javascript" src="http://mediaplayer.yahoo.com/js"></script>

</head>

<body>




<div class="main_content">        
<h3>Track <span py:replace="track.id"/>: <span py:replace="track.title"/><br/>
Main Artist: <span py:replace="track.artist"/><br/>
Album: <span py:replace="track.album"/> (Track <span py:replace="track.tracknum"/>, <span py:replace="track_time"/>)<br/>
MusicBrainz ID: <span py:replace="track.mb_id"/><br/>
<?python import commands; cmd = 'file -b %s' % track.fn_audio; ?>
Audio file info: <span py:replace="commands.getoutput(cmd)"/> (${track.bytes} bytes) <br/>
</h3>
<hr/>


<a title="${track.artist} - ${track.title} (${track.album})" href="/audio/T${track.id}.${track.fn_audio_extension}"></a>|
<span py:for="a in alternate_action">
<span py:content="a">X</span> |
<a href="/download/track_id:${track.id}">Download</a>|
</span>
| <span py:replace="track_mb_id_link"/> |   

<!--span py:replace="yahoo_url"/-->

<a href="/playlist?params=track_id:${track.id}" type="application/xspf+xml"></a>
<hr/>

<table>
<tr>
<td><span py:replace="afeat_graph"/></td>
<td>
<span py:for="f in feat_urllist">
<span py:content="f">X</span><br/>
</span>
</td>
</tr>
</table>


<hr/>
<span py:replace="track_widget(track_widget_data)"/>
<span py:replace="artist_widget(artists)"/>
<span py:replace="album_widget(albums)"/>
<span py:replace="collection_widget(collections)"/>

<hr/>
<table cellpadding="0" cellspacing="1" border="0" class="grid">
  <thead> 
    <tr> <th>Annotation Name</th> <th>Value</th> </tr>
  </thead>
  <tbody>
    <span py:for="a in track.annotations">
      <tr valign="top" class="even">
        <td>${a.name}</td>
        <td>
          <div id="annotation_${a.name}_text">
            <?python annotation_lines = a.value.split('\n') ?>
            <span py:for="line in annotation_lines">
              ${line}
              <br/>
            </span>
          </div>

          <div py:if="a.name in htk_annotation_datatables">
     <script type="text/javascript" src="http://www.google.com/jsapi"></script>
<script type="text/javascript">
  google.load('visualization', '1', {'packages':['annotatedtimeline']});
  
  google.setOnLoadCallback(function () {
    <span py:replace="htk_annotation_datatables[a.name]"/>
    var chart = new google.visualization.AnnotatedTimeLine(document.getElementById('annotation_${a.name}_widget'));
    chart.draw(data, {'dateFormat': 'mm:ss', 'thickness': 3, 'fill': 50,
                      'annotationsWidth': 10, 'displayAnnotations': true,
                      'displayZoomButtons': false});
    google.visualization.events.addListener(chart, 'select', seek_media_player);

    function seek_media_player() {
      var item = chart.getSelection()[0];
      var time = data.getValue(item.row, 0);
      var milliseconds = (time - new Date(time.getFullYear(), time.getMonth(),
                                          time.getDate(), 0, 0, 0, 0));
      YAHOO.MediaPlayer.play(YAHOO.MediaPlayer.mediaObject, milliseconds)
    }
  });
</script>

<div id="annotation_${a.name}_widget" style="width: 500px; height: 250px;"/>
<br/>
        </div>
        </td>
      </tr>
    </span>
  </tbody>
</table>



</div>


</body>

</html>
