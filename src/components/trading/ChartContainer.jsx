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
        const handleResize = () => {
            if (chartRef.current && chartContainerRef.current) {
                chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };

        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: backgroundColor },
                textColor,
            },
            width: chartContainerRef.current.clientWidth,
            height: 400,
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

        const newSeries = chart.addAreaSeries({
            lineColor,
            topColor: areaTopColor,
            bottomColor: areaBottomColor,
        });
        seriesRef.current = newSeries;

        // Initial Data
        if (data && data.length > 0) {
            newSeries.setData(data);
        }

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            if (chart) chart.remove();
        };
    }, [backgroundColor, lineColor, textColor, areaTopColor, areaBottomColor]);

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
