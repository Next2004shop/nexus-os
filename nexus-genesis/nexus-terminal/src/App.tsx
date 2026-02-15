import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import AuthGuard from './components/AuthGuard';
import AppLayout from './components/AppLayout';
import ErrorBoundary from './components/ErrorBoundary';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import PositionsPage from './pages/PositionsPage';
import RiskPage from './pages/RiskPage';
import IntelligencePage from './pages/IntelligencePage';
import ExecutionPage from './pages/ExecutionPage';
import LogsPage from './pages/LogsPage';

function App() {
    return (
        <ErrorBoundary>
            <BrowserRouter>
                <AuthProvider>
                    <Routes>
                        {/* Public */}
                        <Route path="/login" element={<LoginPage />} />

                        {/* Protected — all require JWT */}
                        <Route
                            path="/"
                            element={
                                <AuthGuard>
                                    <AppLayout>
                                        <DashboardPage />
                                    </AppLayout>
                                </AuthGuard>
                            }
                        />
                        <Route
                            path="/positions"
                            element={
                                <AuthGuard>
                                    <AppLayout>
                                        <PositionsPage />
                                    </AppLayout>
                                </AuthGuard>
                            }
                        />
                        <Route
                            path="/risk"
                            element={
                                <AuthGuard>
                                    <AppLayout>
                                        <RiskPage />
                                    </AppLayout>
                                </AuthGuard>
                            }
                        />
                        <Route
                            path="/intelligence"
                            element={
                                <AuthGuard>
                                    <AppLayout>
                                        <IntelligencePage />
                                    </AppLayout>
                                </AuthGuard>
                            }
                        />
                        <Route
                            path="/execution"
                            element={
                                <AuthGuard>
                                    <AppLayout>
                                        <ExecutionPage />
                                    </AppLayout>
                                </AuthGuard>
                            }
                        />
                        <Route
                            path="/logs"
                            element={
                                <AuthGuard>
                                    <AppLayout>
                                        <LogsPage />
                                    </AppLayout>
                                </AuthGuard>
                            }
                        />

                        {/* Catch-all */}
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                </AuthProvider>
            </BrowserRouter>
        </ErrorBoundary>
    );
}

export default App;
