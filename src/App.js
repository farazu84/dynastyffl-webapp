import React, { useState, useEffect } from 'react';
import './App.css';
import Header from './Header';
import Content from './Content';
import League from './views/league/League'
import Team from './views/team/Team'
import Article from './views/article/Article';

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
          </Routes>
        </Router>
      <Footer />
    </div>
  );
}

export default App;
