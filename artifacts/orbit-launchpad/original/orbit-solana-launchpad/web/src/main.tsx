import React from 'react';
import{createRoot}from'react-dom/client';
import{Buffer}from'buffer';
(globalThis as any).Buffer=Buffer;
import('./App').then(({default:App})=>createRoot(document.getElementById('root')!).render(<React.StrictMode><App/></React.StrictMode>));
