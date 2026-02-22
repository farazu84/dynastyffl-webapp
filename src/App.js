import React from 'react';
import './App.css';
import Header from './Header';
import League from './views/league/League'
import Team from './views/team/Team'
import Article from './views/article/Article';
import Rumor from './views/Rumor.js/Rumor';
import News from './views/News/News';
import Archive from './views/archive/Archive';
import TradeTree from './views/archive/TradeTree';
import Footer from './Footer';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { GoogleOAuthProvider } from '@react-oauth/google';


function App() {
  return (
    <GoogleOAuthProvider clientId={process.env.REACT_APP_GOOGLE_CLIENT_ID}>
    <AuthProvider>
      <Router>
        <div className="App">
          <Header />
          <Routes>
            <Route exact path="/" element={<League />} />
            <Route path="/teams/:teamId" element={<Team />} />
            <Route path="/articles/:articleId" element={<Article />} />
            <Route path="/news" element={<News />} />
            <Route path="/rumors" element={<Rumor />} />
            <Route path="/archive/trades/:transactionId" element={<TradeTree />} />
            <Route path="/archive" element={<Archive />} />
          </Routes>
          <Footer />
        </div>
      </Router>
    </AuthProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
