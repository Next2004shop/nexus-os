import React from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import Dashboard from './components/Dashboard';

function App() {
    return (
        <ErrorBoundary>
            <Layout>
                <Dashboard />
            </Layout>
        </ErrorBoundary>
    );
}

export default App;
