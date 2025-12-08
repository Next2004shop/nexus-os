import React, { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

export const ChartContainer = ({ data, colors = {} }) => {
    const chartContainerRef = useRef();
    const chartRef = useRef();
    const seriesRef = useRef();

    const {
        backgroundColor = 'transparent',
        lineColor = '#2962FF',
        textColor = 'rgba(255, 255, 255, 0.9)',
        areaTopColor = '#2962FF',
        areaBottomColor = 'rgba(41, 98, 255, 0.28)',
    } = colors;

    useEffect(() => {


        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: backgroundColor },
                textColor,
            },
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight || 400, // Use container height or fallback
            grid: {
                vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
                horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
            },
            timeScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
                timeVisible: true,
                secondsVisible: false,
            },
            rightPriceScale: {
                borderColor: 'rgba(255, 255, 255, 0.1)',
            },
        });

        chartRef.current = chart;

        try {
            // Switch to Candlestick Series
            const newSeries = chart.addCandlestickSeries({
                upColor: '#00DD80', // Nexus Green
                downColor: '#FF3B30', // Nexus Red
                borderVisible: false,
                wickUpColor: '#00DD80',
                wickDownColor: '#FF3B30',
            });
            seriesRef.current = newSeries;

            // Initial Data
            if (data && data.length > 0) {
                newSeries.setData(data);
            }
        } catch (err) {
            console.error("Failed to add series:", err);
        }

        // Resize Observer
        const resizeObserver = new ResizeObserver(entries => {
            if (entries.length === 0 || !entries[0].target) return;
            const newRect = entries[0].contentRect;
            chart.applyOptions({ width: newRect.width, height: newRect.height });
        });

        resizeObserver.observe(chartContainerRef.current);

        return () => {
            resizeObserver.disconnect();
            if (chart) chart.remove();
        };
    }, [backgroundColor, lineColor, textColor, areaTopColor, areaBottomColor, data]);

    // Update data
    useEffect(() => {
        if (seriesRef.current && data && data.length > 0) {
            // If it's a single update vs full set
            // For simplicity, we just set data again or update the last one
            // Ideally, we should use update() for real-time ticks
            seriesRef.current.setData(data);
        }
    }, [data]);

    return (
        <div ref={chartContainerRef} className="w-full h-full relative" />
    );
};
