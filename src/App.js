import React, { useState, useEffect } from 'react';
import './App.css';
import Header from './Header';
import Content from './Content';
import Footer from './Footer';

function App() {
  const [currentTime, setCurrentTime] = useState(0);

  useEffect(() => {
    fetch('/user/1').then(res => res.json()).then(data => {
      console.log(data)
      //setCurrentTime(data.time);
    });
  }, []);

  return (
    <div className="App">
      <Header />
      <Content />
      <Footer />
    </div>
  );
}

export default App;
