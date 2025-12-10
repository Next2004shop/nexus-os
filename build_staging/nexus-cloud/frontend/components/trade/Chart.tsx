"use client";
import { useEffect, useRef } from "react";
import { createChart, ColorType } from "lightweight-charts";

export const Chart = () => {
    const chartContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: '#8E8E93' },
            grid: { vertLines: { color: 'rgba(255, 255, 255, 0.05)' }, horzLines: { color: 'rgba(255, 255, 255, 0.05)' } },
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
        });

        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth, height: chartContainerRef.current.clientHeight });
            }
        };

        window.addEventListener('resize', handleResize);

        const newSeries = (chart as any).addCandlestickSeries({
            upColor: '#00DD80',
            downColor: '#FF3B30',
            borderVisible: false,
            wickUpColor: '#00DD80',
            wickDownColor: '#FF3B30',
        });

        // Mock Data
        const data = [];
        let time = Math.floor(Date.now() / 1000) - (100 * 3600);
        let value = 98000;
        for (let i = 0; i < 100; i++) {
            const open = value + Math.random() * 100 - 50;
            const close = open + Math.random() * 100 - 50;
            const high = Math.max(open, close) + Math.random() * 20;
            const low = Math.min(open, close) - Math.random() * 20;
            data.push({ time: time + i * 3600, open, high, low, close });
            value = close;
        }
        newSeries.setData(data as any);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, []);

    return <div ref={chartContainerRef} className="w-full h-full" />;
};
