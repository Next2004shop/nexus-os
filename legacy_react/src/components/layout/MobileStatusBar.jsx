import React, { useState, useEffect } from 'react';
import { Wifi, Battery, Signal } from 'lucide-react';

export const MobileStatusBar = () => {
    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    return (
        <div className="md:hidden fixed top-0 left-0 right-0 h-12 px-6 flex justify-between items-center z-[100] text-white font-medium text-sm mix-blend-difference">
            {/* TIME */}
            <div className="tracking-wide">
                {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>

            {/* ICONS */}
            <div className="flex items-center gap-2">
                <Signal size={14} fill="currentColor" />
                <Wifi size={14} />
                <div className="flex items-center gap-1">
                    <span className="text-xs">100%</span>
                    <Battery size={16} fill="currentColor" />
                </div>
            </div>
        </div>
    );
};
