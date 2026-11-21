'use strict';
// ZIP32 writer using the browser's own compression; no external library or upload.
async function iconFolderArchive(files, progress=()=>{}) {
  const table=Array.from({length:256},(_,n)=>{for(let bit=0;bit<8;bit++)n=(n&1)?0xedb88320^(n>>>1):n>>>1;return n>>>0;});
  const crc=data=>{let value=0xffffffff;for(const byte of data)value=table[(value^byte)&255]^(value>>>8);return (value^0xffffffff)>>>0;};
  const local=[],central=[];let offset=0;
  const put=(view,at,value,wide=false)=>wide?view.setUint32(at,value,true):view.setUint16(at,value,true);
  for(let i=0;i<files.length;i++){
    const file=files[i],name=new TextEncoder().encode(file.webkitRelativePath||file.name);
    const source=new Uint8Array(await file.arrayBuffer());let data=source,method=0;
    if(typeof CompressionStream!=='undefined'){
      try{
        const stream=new Blob([source]).stream().pipeThrough(new CompressionStream('deflate-raw'));
        const compressed=new Uint8Array(await new Response(stream).arrayBuffer());
        if(compressed.length<source.length){data=compressed;method=8;}
      }catch{ /* Older browsers can still store small folders uncompressed. */ }
    }
    const checksum=crc(source),header=new Uint8Array(30+name.length),v=new DataView(header.buffer);
    put(v,0,0x04034b50,true);put(v,4,20);put(v,6,0x800);put(v,8,method);put(v,12,0x21);
    put(v,14,checksum,true);put(v,18,data.length,true);put(v,22,source.length,true);put(v,26,name.length);header.set(name,30);
    const record=new Uint8Array(46+name.length),c=new DataView(record.buffer);
    put(c,0,0x02014b50,true);put(c,4,20);put(c,6,20);put(c,8,0x800);put(c,10,method);put(c,14,0x21);
    put(c,16,checksum,true);put(c,20,data.length,true);put(c,24,source.length,true);put(c,28,name.length);put(c,42,offset,true);record.set(name,46);
    local.push(header,data);central.push(record);offset+=header.length+data.length;
    if(offset>32*1024*1024)throw new Error('Das vorbereitete Paket ist größer als 32 MB. Bitte den Ordner in kleinere Pakete aufteilen.');
    progress(i+1,files.length);
  }
  const size=central.reduce((sum,p)=>sum+p.length,0),end=new Uint8Array(22),v=new DataView(end.buffer);
  if(offset+size+22>32*1024*1024)throw new Error('Das vorbereitete Paket ist größer als 32 MB. Bitte in kleinere Pakete aufteilen.');
  put(v,0,0x06054b50,true);put(v,8,files.length);put(v,10,files.length);put(v,12,size,true);put(v,16,offset,true);
  const output=new Uint8Array(offset+size+22);let at=0;
  for(const part of [...local,...central,end]){output.set(part,at);at+=part.length;}
  return output;
}
