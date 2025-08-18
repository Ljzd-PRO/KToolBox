import React from 'react';
import './App.css';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './components/Dashboard';
import { DownloadPost } from './components/DownloadPost';
import { SyncCreator } from './components/SyncCreator';
import { SearchCreator } from './components/SearchCreator';
import { SearchCreatorPost } from './components/SearchCreatorPost';
import { Tasks } from './components/Tasks';
import { Settings } from './components/Settings';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/download-post" element={<DownloadPost />} />
          <Route path="/sync-creator" element={<SyncCreator />} />
          <Route path="/search-creator" element={<SearchCreator />} />
          <Route path="/search-creator-post" element={<SearchCreatorPost />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
