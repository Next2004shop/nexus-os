import React from 'react';
import { Scale, CheckCircle, AlertCircle, DollarSign, Calendar } from 'lucide-react';

export const TaxPage = () => {
    const taxRate = 0.25; // 25% Corporate Tax
    const revenue = 1250000.00;
    const expenses = 450000.00;
    const taxableIncome = revenue - expenses;
    const estimatedTax = taxableIncome * taxRate;
    const taxPaid = 150000.00;
    const taxDue = estimatedTax - taxPaid;

    return (
        <div className="p-6 space-y-6 animate-fadeIn pb-24 md:pb-6">
            {/* HEADER */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Scale className="text-nexus-green" /> Tax Compliance
                    </h1>
                    <p className="text-nexus-subtext">Automated Liability Tracking & Payments</p>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-nexus-green/10 border border-nexus-green/20 rounded-lg">
                    <CheckCircle size={18} className="text-nexus-green" />
                    <span className="text-nexus-green font-bold text-sm">STATUS: COMPLIANT</span>
                </div>
            </div>

            {/* PEACE OF MIND BANNER */}
            <div className="bg-gradient-to-r from-nexus-green/20 to-transparent border border-nexus-green/20 p-6 rounded-xl flex items-center justify-between">
                <div>
                    <h3 className="text-xl font-bold text-white mb-2">Peace of Mind Protocol Active</h3>
                    <p className="text-nexus-subtext max-w-xl">
                        Nexus automatically sets aside 25% of all realized profits into a segregated "Tax Vault".
                        You are fully covered for the upcoming fiscal year. No surprises.
                    </p>
                </div>
                <div className="hidden md:block">
                    <Scale size={64} className="text-nexus-green opacity-20" />
                </div>
            </div>

            {/* TAX CALCULATOR */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-card border border-white/5 p-6 rounded-xl">
                    <h3 className="text-nexus-subtext text-xs uppercase font-bold mb-4">Taxable Income (YTD)</h3>
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                            <span className="text-nexus-subtext">Gross Revenue</span>
                            <span className="text-white">${revenue.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-nexus-subtext">Deductible Expenses</span>
                            <span className="text-nexus-red">-${expenses.toLocaleString()}</span>
                        </div>
                        <div className="h-px bg-white/10 my-2"></div>
                        <div className="flex justify-between font-bold">
                            <span className="text-white">Net Taxable</span>
                            <span className="text-nexus-yellow">${taxableIncome.toLocaleString()}</span>
                        </div>
                    </div>
                </div>

                <div className="bg-card border border-white/5 p-6 rounded-xl">
                    <h3 className="text-nexus-subtext text-xs uppercase font-bold mb-4">Liability Breakdown</h3>
                    <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                            <span className="text-nexus-subtext">Est. Tax (25%)</span>
                            <span className="text-white">${estimatedTax.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                            <span className="text-nexus-subtext">Already Paid</span>
                            <span className="text-nexus-green">-${taxPaid.toLocaleString()}</span>
                        </div>
                        <div className="h-px bg-white/10 my-2"></div>
                        <div className="flex justify-between font-bold">
                            <span className="text-white">Remaining Due</span>
                            <span className="text-white">${taxDue.toLocaleString()}</span>
                        </div>
                    </div>
                </div>

                <div className="bg-card border border-white/5 p-6 rounded-xl flex flex-col justify-center items-center text-center">
                    <div className="w-16 h-16 bg-nexus-green/10 rounded-full flex items-center justify-center mb-4">
                        <Calendar size={32} className="text-nexus-green" />
                    </div>
                    <h3 className="text-white font-bold">Next Filing Date</h3>
                    <p className="text-2xl font-mono text-nexus-green mt-2">April 15, 2026</p>
                    <button className="mt-4 btn-secondary text-xs w-full">ADD TO CALENDAR</button>
                </div>
            </div>

            {/* ACTION BUTTONS */}
            <div className="flex justify-end gap-4">
                <button className="btn-secondary flex items-center gap-2">
                    <DollarSign size={18} />
                    MAKE PRE-PAYMENT
                </button>
                <button className="btn-primary flex items-center gap-2">
                    <CheckCircle size={18} />
                    FILE RETURN NOW
                </button>
            </div>
        </div>
    );
};
