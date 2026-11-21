const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
vm.runInThisContext(fs.readFileSync('ugso_usbhub/static/archive.js','utf8'));
(async()=>{
 const files=[{name:'manifest.json',webkitRelativePath:'Pack/manifest.json',arrayBuffer:async()=>new TextEncoder().encode('{"Name":"Test"}').buffer},
  {name:'Grün.svg',webkitRelativePath:'Pack/icons/Grün.svg',arrayBuffer:async()=>new TextEncoder().encode('<svg>'+('test'.repeat(1000))+'</svg>').buffer}];
 const progress=[];const zip=await iconFolderArchive(files,(i,n)=>progress.push([i,n]));
 assert.deepEqual(progress,[[1,2],[2,2]]);
 const result=execFileSync('python',['-c','import sys,zipfile,io,json;z=zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read()));assert z.testzip() is None;assert len(z.namelist())==2;assert json.loads(z.read("Pack/manifest.json"))["Name"]=="Test";assert len(z.read(z.namelist()[1]))>4000;print("ZIP names, UTF-8, CRC and decompression OK")'],{input:zip,encoding:'utf8'});
 console.log(result.trim());
})().catch(e=>{console.error(e);process.exitCode=1;});
