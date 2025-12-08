import { useState } from 'react';
import { Bell, Shield, TrendingUp, Info, Check, AlertTriangle, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../context/ToastContext';

const MOCK_NOTIFICATIONS = [
    { id: 1, type: 'security', title: 'New Login Detected', message: 'New login from iPhone 14 Pro in Nairobi, Kenya.', time: '2 min ago', read: false },
    { id: 2, type: 'trade', title: 'Deposit Successful', message: 'Your deposit of $5,000.00 has been credited.', time: '1 hour ago', read: false },
    { id: 3, type: 'system', title: 'System Maintenance', message: 'Scheduled maintenance on Nov 28, 02:00 UTC.', time: '5 hours ago', read: true },
    { id: 4, type: 'trade', title: 'Bitcoin Surge', message: 'BTC is up 5% in the last hour! Check the charts.', time: '1 day ago', read: true },
    { id: 5, type: 'security', title: 'Password Changed', message: 'Your account password was successfully updated.', time: '2 days ago', read: true },
    { id: 6, type: 'system', title: 'Welcome to Nexus', message: 'Thanks for joining the world\'s most advanced trading platform.', time: '1 week ago', read: true },
];

const NotificationItem = ({ item }) => {
    const getIcon = () => {
        switch (item.type) {
            case 'security': return <Shield size={20} className="text-nexus-red" />;
            case 'trade': return <TrendingUp size={20} className="text-nexus-green" />;
            case 'system': return <Info size={20} className="text-nexus-blue" />;
            default: return <Bell size={20} className="text-nexus-yellow" />;
        }
    };

    return (
        <div className={`flex gap-4 p-4 border-b border-nexus-border hover:bg-white/5 transition-colors ${!item.read ? 'bg-white/5' : ''}`}>
            <div className={`w-10 h-10 rounded-full flex items-center justify-center bg-nexus-border shrink-0`}>
                {getIcon()}
            </div>
            <div className="flex-1">
                <div className="flex justify-between items-start">
                    <h3 className={`text-sm font-bold ${!item.read ? 'text-white' : 'text-nexus-text'}`}>{item.title}</h3>
                    <span className="text-xs text-nexus-subtext">{item.time}</span>
                </div>
                <p className="text-xs text-nexus-subtext mt-1 leading-relaxed">{item.message}</p>
            </div>
            {!item.read && (
                <div className="w-2 h-2 rounded-full bg-nexus-yellow mt-2"></div>
            )}
        </div>
    );
};

export const NotificationsPage = () => {
    const navigate = useNavigate();
    const [activeTab, setActiveTab] = useState('all');
    const [notifications, setNotifications] = useState(MOCK_NOTIFICATIONS);

    const filteredNotifications = activeTab === 'all'
        ? notifications
        : notifications.filter(n => n.type === activeTab);

    const { toast } = useToast();

    const markAllRead = () => {
        setNotifications(notifications.map(n => ({ ...n, read: true })));
        toast.success("All notifications marked as read");
    };

    return (
        <div className="bg-nexus-black min-h-screen pb-20">
            {/* Header */}
            <div className="sticky top-0 z-30 bg-nexus-black/95 backdrop-blur-md border-b border-nexus-border px-4 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <button onClick={() => navigate(-1)} className="text-nexus-subtext hover:text-white">
                        <X size={24} />
                    </button>
                    <h1 className="text-lg font-bold text-white">Notifications</h1>
                </div>
                <button onClick={markAllRead} className="text-xs font-bold text-nexus-yellow hover:text-white transition-colors">
                    Mark all read
                </button>
            </div>

            {/* Tabs */}
            <div className="flex px-4 border-b border-nexus-border overflow-x-auto no-scrollbar">
                {['all', 'trade', 'security', 'system'].map(tab => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-3 text-sm font-bold capitalize whitespace-nowrap relative ${activeTab === tab ? 'text-white' : 'text-nexus-subtext'
                            }`}
                    >
                        {tab}
                        {activeTab === tab && (
                            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-nexus-yellow"></div>
                        )}
                    </button>
                ))}
            </div>

            {/* List */}
            <div className="mt-2">
                {filteredNotifications.length > 0 ? (
                    filteredNotifications.map(item => (
                        <NotificationItem key={item.id} item={item} />
                    ))
                ) : (
                    <div className="flex flex-col items-center justify-center py-20 text-nexus-subtext">
                        <Bell size={48} className="mb-4 opacity-20" />
                        <p>No notifications</p>
                    </div>
                )}
            </div>
        </div>
    );
};
