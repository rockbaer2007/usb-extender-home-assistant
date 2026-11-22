'use strict';
let mobileQr=null;
function mobile() {
  const options=config.mobile||={enabled:false,host:'0.0.0.0',port:28198,advertise_host:location.hostname,columns:5,rows:3};
  const c=card('Stream-Deck-Mobile-Server · experimentell');
  c.append(el('p','Verbindet die Android-App per QR-Code direkt mit diesem Raspberry Pi. Kopplung, Icons und Tasteneingaben sind vom Nutzer bestätigt; weitere Praxistests laufen. Das Raster kommt von der Android-App; keine Pro-Stufe im Server.'));
  field(c,'Stream-Deck-Mobile-Server aktivieren',options.enabled,v=>{options.enabled=v;mobileQr=null;},'checkbox');
  const fields=el('div',undefined,'fields');c.append(fields);
  field(fields,'Raspberry-Pi-Adresse für den QR-Code',options.advertise_host,v=>{options.advertise_host=v;mobileQr=null;});
  const port=field(fields,'Mobile-Port',options.port,v=>{options.port=v;mobileQr=null;},'number');port.min=1024;port.max=65535;
  c.append(el('p','Zeilen und Spalten ausschließlich in der Android-App einstellen. Das gemeldete Raster wird ohne Verbindungstrennung übernommen. Offline bleibt die zuletzt empfangene Ansicht erhalten.'));
  c.append(el('p','Bei verbundenem Mobile-Deck öffnet sich der Editor automatisch; ungespeicherte Änderungen bleiben geschützt.'));
  c.append(el('small','Bis zu 64 bereitgestellte Tasten. Die sichtbare Tastenanzahl und das Raster in Android können von den App-Einstellungen abhängen.'));
  c.append(el('p','IPv4-Adresse oder erreichbaren Hostnamen des Pi eintragen und oben speichern. Der Mobile-Dienst läuft unabhängig von der Weboberfläche. Zum Koppeln muss diese erreichbar sein; danach darf sie abgeschaltet werden.'));
  const tools=el('div',undefined,'toolbar');c.append(tools);
  button(tools,'Kopplung starten · QR-Code',async()=>{
    if(changed)throw new Error('Änderungen zuerst oben speichern.');
    if(!status.mobile?.active)throw new Error('Mobile-Dienst noch nicht aktiv. Speichern und Status abwarten.');
    await api('mobile/control',{action:'open'});mobileQr=await api('mobile/qr',{});status=await api('status');render();
  },'primary');
  button(tools,'Kopplungsfenster schließen',async()=>{await api('mobile/control',{action:'close'});mobileQr=null;render();});
  if(mobileQr){
    const qr=el('img');qr.src='data:image/png;base64,'+mobileQr.qr;qr.alt='QR-Code zum Koppeln mit Stream Deck Mobile';qr.className='mobile-qr';c.append(qr,el('p','In Stream Deck Mobile „Computer hinzufügen“ wählen und diesen Code scannen. Anschließend die Anfrage und den Prüfabdruck hier bestätigen.'));
    const link=el('code',mobileQr.url);c.append(link);
  }
  const state=card('Mobile-Verbindungen'),box=el('div');box.id='mobile-status';state.append(box);renderMobileStatus(box);
  const steps=card('Nach der Kopplung');
  const list=el('ol');['In der Android-App ein neues virtuelles Deck anlegen oder ein vorhandenes auswählen.','Unter „USB / Virtuelle Geräte“ oder im Tab „Stream Deck“ das neue Mobile-Gerät freigeben und speichern.','Im grafischen Stream-Deck-Tab Tasten auswählen, Bilder gestalten und MQTT-Aktionen zuordnen.','Android-Taste drücken und unter „Tasten & Anzeigen“ die MQTT-Übertragung prüfen.'].forEach(text=>list.append(el('li',text)));steps.append(list);
  steps.append(el('p','Die Verbindung nutzt einen separaten lokalen WebSocket-Port. Kein Bonjour- oder Cloud-Discovery-Server enthalten: Einrichtung über QR-Code. Bildschirmhelligkeit am Android-Gerät einstellen.','muted'));
}
function renderMobileStatus(parent) {
  parent.replaceChildren();const value=status.mobile||{};
  parent.append(el('p',value.active?'Mobile-Dienst aktiv':'Mobile-Dienst aus / noch nicht gestartet',value.active?'badge':'warning'));
  if(value.error)parent.append(el('p',value.error,'warning'));
  if(value.pairing_until>Date.now()/1000)parent.append(el('p','Kopplungsfenster geöffnet (maximal zwei Minuten).'));
  (value.pending||[]).forEach(request=>{
    const row=el('div',undefined,'deck-binding');parent.append(row);
    row.append(el('h3','Kopplung bestätigen · '+request.name),el('p',request.fingerprint,'mobile-fingerprint'),el('p','Prüfabdruck mit dem Tablet vergleichen und nur bei Übereinstimmung bestätigen.'));
    const actions=el('div',undefined,'row');row.append(actions);
    button(actions,'Gerät vertrauen',async()=>{await api('mobile/control',{action:'allow',token:request.token});notice('Bestätigung gesendet. Der Verbindungsstatus wird automatisch aktualisiert.');},'primary');
    button(actions,'Ablehnen',async()=>{await api('mobile/control',{action:'deny',token:request.token});notice('Ablehnung gesendet.');},'danger');
  });
  if(!(value.clients||[]).length)parent.append(el('p','Noch kein Mobilgerät verbunden.'));
  (value.clients||[]).forEach(client=>parent.append(el('p',client.name+' · '+(client.authorized?'Vertrauenswürdig':'Kopplung ausstehend')+(client.device?' · Deck geöffnet':''))));
  (value.clients||[]).filter(client=>client.device&&client.images_sent!==undefined).forEach(client=>parent.append(el('small','Gesendete Tastenbilder: '+client.images_sent+' · Anzeige-Metadaten: '+client.contexts_sent+' · Ohne Änderungen sollen diese Zähler stehen bleiben.')));
  (value.clients||[]).filter(client=>client.pings_sent!==undefined).forEach(client=>parent.append(el('small','Keepalive: '+client.pings_sent+' Ping / '+client.pongs_received+' Pong · Verbindungspflege ohne Bildübertragung.')));
  (status.devices||[]).filter(d=>d.connection==='mobile'&&d.deck).forEach(d=>parent.append(el('p',d.name+' · '+d.deck.layout[0]+' Zeilen hoch × '+d.deck.layout[1]+' Spalten breit · '+(d.deck.layout_source==='tablet'?'vom Tablet gemeldet':'noch keine Rastermeldung vom Tablet'))));
  if(value.recent_disconnects?.length){const last=value.recent_disconnects.at(-1);parent.append(el('p','Letzte Trennung: '+last.name+' · '+last.reason+' · '+last.images_sent+' Bilder / '+last.contexts_sent+' Metadatenpakete','muted'));}
  if(value.trusted?.length){
    parent.append(el('small','Gespeichertes Vertrauen bleibt nach Neustart erhalten. Widerrufen sperrt dieses Mobilgerät; Decks und Zuordnungen bleiben gespeichert.'));
    for(const client of value.trusted){const row=el('div',undefined,'row');row.append(el('span',client.name));button(row,'Kopplung widerrufen',async()=>{if(confirm('Vertrauen für „'+client.name+'“ widerrufen? Aktive Verbindungen werden geschlossen. Erneute Nutzung erfordert eine neue Bestätigung.'))await deviceAction('revoke',client.id);},'danger');parent.append(row);}
  }
}
