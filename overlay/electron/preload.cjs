const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('overlay', {
  version: '0.1.0',
});
