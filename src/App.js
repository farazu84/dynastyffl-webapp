import React, { useState, useEffect } from 'react';
import './App.css';
import Header from './Header';
import Content from './Content';
import League from './views/league/League'
import Team from './views/team/Team'
import Article from './views/article/Article';
import Rumor from './views/Rumor.js/Rumor';
import News from './views/News/News';
import Footer from './Footer';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';

{/*import { Route, Routes, useHistory } from 'react-router-dom';*/}

function App() {
  return (
    <div className="App">
      <Header />
        <Router>
          <Routes>
            <Route exact path="/" element={<League />} />
            <Route path="/teams/:teamId" element={<Team />} />
            <Route path="/articles/:articleId" element={<Article />} />
            <Route path="/news" element={<News />} />
            <Route path="/rumors" element={<Rumor />} />
          </Routes>
        </Router>
      <Footer />
    </div>
  );
}

export default App;
