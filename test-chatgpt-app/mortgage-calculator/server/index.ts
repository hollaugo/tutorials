// Mortgage Calculator - ChatGPT App
// Calculates mortgage payments, compares down payment options, and visualizes amortization

import "dotenv/config";
import express, { Request, Response } from "express";
import { randomUUID } from "crypto";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ListResourcesRequestSchema,
  ReadResourceRequestSchema,
  JSONRPCMessage,
} from "@modelcontextprotocol/sdk/types.js";

// Configuration
const PORT = process.env.PORT || 3000;
const NODE_ENV = process.env.NODE_ENV || "development";
const WIDGET_DOMAIN = process.env.WIDGET_DOMAIN || `http://localhost:${PORT}`;

function log(...args: unknown[]) {
  if (NODE_ENV === "development") {
    console.log(`[${new Date().toISOString()}]`, ...args);
  }
}

// ============================================================================
// MORTGAGE CALCULATION LOGIC
// ============================================================================

interface MortgageInput {
  homePrice: number;
  downPaymentPercent: number;
  interestRate: number;
  loanTermYears: number;
  propertyTaxRate?: number;      // Annual rate as percentage (e.g., 1.2)
  homeInsuranceAnnual?: number;  // Annual insurance cost
  pmiRate?: number;              // PMI rate if down payment < 20%
}

interface MortgageResult {
  homePrice: number;
  downPayment: number;
  downPaymentPercent: number;
  loanAmount: number;
  interestRate: number;
  loanTermYears: number;
  monthlyPrincipalInterest: number;
  monthlyPropertyTax: number;
  monthlyInsurance: number;
  monthlyPMI: number;
  totalMonthlyPayment: number;
  totalInterestPaid: number;
  totalCost: number;
}

interface AmortizationEntry {
  period: number;
  year: number;
  month: number;
  payment: number;
  principal: number;
  interest: number;
  balance: number;
  totalPrincipalPaid: number;
  totalInterestPaid: number;
}

function calculateMortgage(input: MortgageInput): MortgageResult {
  const {
    homePrice,
    downPaymentPercent,
    interestRate,
    loanTermYears,
    propertyTaxRate = 1.2,
    homeInsuranceAnnual = 1200,
    pmiRate = 0.5,
  } = input;

  const downPayment = homePrice * (downPaymentPercent / 100);
  const loanAmount = homePrice - downPayment;
  const monthlyRate = interestRate / 100 / 12;
  const numPayments = loanTermYears * 12;

  // Monthly principal & interest (P&I)
  let monthlyPrincipalInterest: number;
  if (monthlyRate === 0) {
    monthlyPrincipalInterest = loanAmount / numPayments;
  } else {
    monthlyPrincipalInterest =
      (loanAmount * monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
      (Math.pow(1 + monthlyRate, numPayments) - 1);
  }

  // Property tax (monthly)
  const monthlyPropertyTax = (homePrice * (propertyTaxRate / 100)) / 12;

  // Home insurance (monthly)
  const monthlyInsurance = homeInsuranceAnnual / 12;

  // PMI (if down payment < 20%)
  const monthlyPMI = downPaymentPercent < 20
    ? (loanAmount * (pmiRate / 100)) / 12
    : 0;

  const totalMonthlyPayment =
    monthlyPrincipalInterest + monthlyPropertyTax + monthlyInsurance + monthlyPMI;

  const totalInterestPaid = monthlyPrincipalInterest * numPayments - loanAmount;
  const totalCost = downPayment + monthlyPrincipalInterest * numPayments +
    (monthlyPropertyTax + monthlyInsurance) * numPayments +
    monthlyPMI * Math.min(numPayments, 12 * 10); // PMI typically for ~10 years max

  return {
    homePrice,
    downPayment,
    downPaymentPercent,
    loanAmount,
    interestRate,
    loanTermYears,
    monthlyPrincipalInterest: Math.round(monthlyPrincipalInterest * 100) / 100,
    monthlyPropertyTax: Math.round(monthlyPropertyTax * 100) / 100,
    monthlyInsurance: Math.round(monthlyInsurance * 100) / 100,
    monthlyPMI: Math.round(monthlyPMI * 100) / 100,
    totalMonthlyPayment: Math.round(totalMonthlyPayment * 100) / 100,
    totalInterestPaid: Math.round(totalInterestPaid * 100) / 100,
    totalCost: Math.round(totalCost * 100) / 100,
  };
}

function generateAmortizationSchedule(
  input: MortgageInput,
  granularity: "monthly" | "yearly" = "yearly"
): AmortizationEntry[] {
  const result = calculateMortgage(input);
  const monthlyRate = input.interestRate / 100 / 12;
  const numPayments = input.loanTermYears * 12;

  const schedule: AmortizationEntry[] = [];
  let balance = result.loanAmount;
  let totalPrincipalPaid = 0;
  let totalInterestPaid = 0;

  for (let period = 1; period <= numPayments; period++) {
    const interestPayment = balance * monthlyRate;
    const principalPayment = result.monthlyPrincipalInterest - interestPayment;
    balance -= principalPayment;
    totalPrincipalPaid += principalPayment;
    totalInterestPaid += interestPayment;

    const year = Math.ceil(period / 12);
    const month = ((period - 1) % 12) + 1;

    if (granularity === "monthly" || month === 12 || period === numPayments) {
      schedule.push({
        period,
        year,
        month,
        payment: Math.round(result.monthlyPrincipalInterest * 100) / 100,
        principal: Math.round(principalPayment * 100) / 100,
        interest: Math.round(interestPayment * 100) / 100,
        balance: Math.round(Math.max(0, balance) * 100) / 100,
        totalPrincipalPaid: Math.round(totalPrincipalPaid * 100) / 100,
        totalInterestPaid: Math.round(totalInterestPaid * 100) / 100,
      });
    }
  }

  return granularity === "yearly"
    ? schedule.filter((_, i) => (i + 1) % 12 === 0 || i === schedule.length - 1)
    : schedule;
}

// ============================================================================
// WIDGET CONFIGURATION
// ============================================================================

interface WidgetConfig {
  id: string;
  name: string;
  description: string;
  templateUri: string;
  invoking: string;
  invoked: string;
  mockData: Record<string, unknown>;
}

const widgets: WidgetConfig[] = [
  {
    id: "mortgage-summary",
    name: "Mortgage Summary",
    description: "Displays a detailed mortgage payment breakdown with visual charts",
    templateUri: "ui://widget/mortgage-summary.html",
    invoking: "Calculating mortgage...",
    invoked: "Mortgage calculated",
    mockData: {
      homePrice: 450000,
      downPayment: 90000,
      downPaymentPercent: 20,
      loanAmount: 360000,
      interestRate: 6.5,
      loanTermYears: 30,
      monthlyPrincipalInterest: 2275.44,
      monthlyPropertyTax: 450,
      monthlyInsurance: 100,
      monthlyPMI: 0,
      totalMonthlyPayment: 2825.44,
      totalInterestPaid: 459158.4,
      totalCost: 909158.4,
    },
  },
  {
    id: "down-payment-comparison",
    name: "Down Payment Comparison",
    description: "Compares different down payment scenarios side by side",
    templateUri: "ui://widget/down-payment-comparison.html",
    invoking: "Comparing scenarios...",
    invoked: "Comparison ready",
    mockData: {
      homePrice: 450000,
      interestRate: 6.5,
      loanTermYears: 30,
      scenarios: [
        { downPaymentPercent: 10, downPayment: 45000, monthlyPayment: 2811.24, totalCost: 1057045 },
        { downPaymentPercent: 15, downPayment: 67500, monthlyPayment: 2665.89, totalCost: 1027720 },
        { downPaymentPercent: 20, downPayment: 90000, monthlyPayment: 2520.54, totalCost: 997394 },
        { downPaymentPercent: 25, downPayment: 112500, monthlyPayment: 2375.19, totalCost: 967069 },
      ],
    },
  },
  {
    id: "amortization-chart",
    name: "Amortization Chart",
    description: "Shows the loan amortization schedule over time with principal vs interest breakdown",
    templateUri: "ui://widget/amortization-chart.html",
    invoking: "Generating amortization schedule...",
    invoked: "Amortization schedule ready",
    mockData: {
      homePrice: 450000,
      downPaymentPercent: 20,
      loanAmount: 360000,
      interestRate: 6.5,
      loanTermYears: 30,
      schedule: [
        { year: 5, balance: 335000, totalPrincipalPaid: 25000, totalInterestPaid: 110000 },
        { year: 10, balance: 300000, totalPrincipalPaid: 60000, totalInterestPaid: 200000 },
        { year: 15, balance: 250000, totalPrincipalPaid: 110000, totalInterestPaid: 270000 },
        { year: 20, balance: 180000, totalPrincipalPaid: 180000, totalInterestPaid: 330000 },
        { year: 25, balance: 90000, totalPrincipalPaid: 270000, totalInterestPaid: 380000 },
        { year: 30, balance: 0, totalPrincipalPaid: 360000, totalInterestPaid: 420000 },
      ],
    },
  },
];

const WIDGETS_BY_ID = new Map(widgets.map((w) => [w.id, w]));
const WIDGETS_BY_URI = new Map(widgets.map((w) => [w.templateUri, w]));

// ============================================================================
// WIDGET HTML GENERATORS
// ============================================================================

function generateMortgageSummaryHtml(previewData?: Record<string, unknown>): string {
  const previewScript = previewData
    ? `<script>window.PREVIEW_DATA = ${JSON.stringify(previewData)};</script>`
    : "";

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mortgage Summary</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      padding: 20px;
    }
    .container {
      max-width: 600px;
      margin: 0 auto;
    }
    .card {
      background: white;
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    .header {
      text-align: center;
      margin-bottom: 24px;
    }
    .header h1 {
      font-size: 24px;
      color: #1a1a2e;
      margin-bottom: 8px;
    }
    .header .home-price {
      font-size: 32px;
      font-weight: 700;
      color: #667eea;
    }
    .monthly-payment {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 12px;
      padding: 20px;
      text-align: center;
      margin-bottom: 24px;
    }
    .monthly-payment .label {
      color: rgba(255,255,255,0.8);
      font-size: 14px;
      margin-bottom: 4px;
    }
    .monthly-payment .amount {
      color: white;
      font-size: 42px;
      font-weight: 700;
    }
    .monthly-payment .per-month {
      color: rgba(255,255,255,0.8);
      font-size: 14px;
    }
    .breakdown {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 24px;
    }
    .breakdown-item {
      background: #f8f9ff;
      border-radius: 10px;
      padding: 16px;
    }
    .breakdown-item .label {
      font-size: 12px;
      color: #666;
      margin-bottom: 4px;
    }
    .breakdown-item .value {
      font-size: 18px;
      font-weight: 600;
      color: #1a1a2e;
    }
    .chart-section {
      margin-bottom: 24px;
    }
    .chart-section h3 {
      font-size: 16px;
      color: #1a1a2e;
      margin-bottom: 12px;
    }
    .donut-container {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 24px;
    }
    .donut-chart {
      width: 140px;
      height: 140px;
    }
    .legend {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
    }
    .legend-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
    }
    .summary-row {
      display: flex;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid #eee;
    }
    .summary-row:last-child {
      border-bottom: none;
    }
    .summary-row .label {
      color: #666;
    }
    .summary-row .value {
      font-weight: 600;
      color: #1a1a2e;
    }
    .pmi-badge {
      display: inline-block;
      background: #ff6b6b;
      color: white;
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 10px;
      margin-left: 8px;
    }
    .loading {
      text-align: center;
      padding: 40px;
      color: #666;
    }
  </style>
  ${previewScript}
</head>
<body>
  <div class="container">
    <div class="card">
      <div id="root"><div class="loading">Loading mortgage details...</div></div>
    </div>
  </div>
  <script>
    (function() {
      let rendered = false;

      function formatCurrency(num) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(num);
      }

      function formatCurrencyDecimals(num) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num);
      }

      function createDonutChart(data) {
        const total = data.reduce((sum, d) => sum + d.value, 0);
        let cumulative = 0;
        const size = 140;
        const strokeWidth = 25;
        const radius = (size - strokeWidth) / 2;
        const circumference = 2 * Math.PI * radius;

        let paths = '';
        data.forEach((item, i) => {
          const percentage = item.value / total;
          const dashLength = percentage * circumference;
          const dashOffset = (cumulative / total) * circumference;
          paths += '<circle cx="' + (size/2) + '" cy="' + (size/2) + '" r="' + radius + '" fill="none" stroke="' + item.color + '" stroke-width="' + strokeWidth + '" stroke-dasharray="' + dashLength + ' ' + circumference + '" stroke-dashoffset="-' + dashOffset + '" transform="rotate(-90 ' + (size/2) + ' ' + (size/2) + ')"/>';
          cumulative += item.value;
        });

        return '<svg class="donut-chart" viewBox="0 0 ' + size + ' ' + size + '">' + paths + '</svg>';
      }

      function render(data) {
        if (rendered || !data) return;
        rendered = true;

        const hasPMI = data.monthlyPMI > 0;

        const breakdownData = [
          { label: 'Principal & Interest', value: data.monthlyPrincipalInterest, color: '#667eea' },
          { label: 'Property Tax', value: data.monthlyPropertyTax, color: '#48bb78' },
          { label: 'Insurance', value: data.monthlyInsurance, color: '#ed8936' },
        ];
        if (hasPMI) {
          breakdownData.push({ label: 'PMI', value: data.monthlyPMI, color: '#ff6b6b' });
        }

        const donutChart = createDonutChart(breakdownData);
        const legendHtml = breakdownData.map(d =>
          '<div class="legend-item"><span class="legend-dot" style="background:' + d.color + '"></span>' + d.label + ': ' + formatCurrencyDecimals(d.value) + '</div>'
        ).join('');

        document.getElementById('root').innerHTML =
          '<div class="header">' +
            '<h1>Mortgage Summary</h1>' +
            '<div class="home-price">' + formatCurrency(data.homePrice) + ' Home</div>' +
          '</div>' +
          '<div class="monthly-payment">' +
            '<div class="label">Total Monthly Payment</div>' +
            '<div class="amount">' + formatCurrencyDecimals(data.totalMonthlyPayment) + '</div>' +
            '<div class="per-month">per month</div>' +
          '</div>' +
          '<div class="breakdown">' +
            '<div class="breakdown-item"><div class="label">Down Payment (' + data.downPaymentPercent + '%)</div><div class="value">' + formatCurrency(data.downPayment) + '</div></div>' +
            '<div class="breakdown-item"><div class="label">Loan Amount</div><div class="value">' + formatCurrency(data.loanAmount) + '</div></div>' +
            '<div class="breakdown-item"><div class="label">Interest Rate</div><div class="value">' + data.interestRate + '%</div></div>' +
            '<div class="breakdown-item"><div class="label">Loan Term</div><div class="value">' + data.loanTermYears + ' years</div></div>' +
          '</div>' +
          '<div class="chart-section">' +
            '<h3>Monthly Payment Breakdown</h3>' +
            '<div class="donut-container">' + donutChart + '<div class="legend">' + legendHtml + '</div></div>' +
          '</div>' +
          '<div class="summary-section">' +
            '<div class="summary-row"><span class="label">Total Interest Paid</span><span class="value">' + formatCurrency(data.totalInterestPaid) + '</span></div>' +
            '<div class="summary-row"><span class="label">Total Cost (over ' + data.loanTermYears + ' years)</span><span class="value">' + formatCurrency(data.totalCost) + '</span></div>' +
            (hasPMI ? '<div class="summary-row"><span class="label">PMI Status</span><span class="value">Required<span class="pmi-badge">Until 20% equity</span></span></div>' : '') +
          '</div>';
      }

      function tryRender() {
        if (window.PREVIEW_DATA) { render(window.PREVIEW_DATA); return; }
        if (window.openai?.toolOutput) { render(window.openai.toolOutput); }
      }

      window.addEventListener('openai:set_globals', tryRender);

      const poll = setInterval(() => {
        if (window.openai?.toolOutput || window.PREVIEW_DATA) {
          tryRender();
          clearInterval(poll);
        }
      }, 100);
      setTimeout(() => clearInterval(poll), 10000);

      tryRender();
    })();
  </script>
</body>
</html>`;
}

function generateDownPaymentComparisonHtml(previewData?: Record<string, unknown>): string {
  const previewScript = previewData
    ? `<script>window.PREVIEW_DATA = ${JSON.stringify(previewData)};</script>`
    : "";

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Down Payment Comparison</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
      min-height: 100vh;
      padding: 20px;
    }
    .container {
      max-width: 700px;
      margin: 0 auto;
    }
    .card {
      background: white;
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    .header {
      text-align: center;
      margin-bottom: 24px;
    }
    .header h1 {
      font-size: 24px;
      color: #1a1a2e;
      margin-bottom: 8px;
    }
    .header .subtitle {
      color: #666;
      font-size: 14px;
    }
    .scenarios {
      display: grid;
      gap: 16px;
    }
    .scenario {
      display: grid;
      grid-template-columns: 80px 1fr 120px;
      align-items: center;
      gap: 16px;
      padding: 16px;
      background: #f8f9ff;
      border-radius: 12px;
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .scenario:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .scenario.best {
      background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
      color: white;
    }
    .scenario.best .monthly-label,
    .scenario.best .savings {
      color: rgba(255,255,255,0.8);
    }
    .down-percent {
      font-size: 28px;
      font-weight: 700;
      text-align: center;
    }
    .bar-container {
      height: 40px;
      position: relative;
    }
    .bar {
      height: 100%;
      border-radius: 8px;
      display: flex;
      align-items: center;
      padding-left: 12px;
      font-weight: 600;
      font-size: 14px;
      color: white;
      transition: width 0.5s ease-out;
    }
    .bar.pmi {
      background: linear-gradient(90deg, #ff6b6b 0%, #ee5a5a 100%);
    }
    .bar.no-pmi {
      background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
    }
    .monthly-info {
      text-align: right;
    }
    .monthly-amount {
      font-size: 20px;
      font-weight: 700;
    }
    .monthly-label {
      font-size: 11px;
      color: #666;
    }
    .savings {
      font-size: 12px;
      color: #11998e;
      font-weight: 500;
    }
    .chart-container {
      margin-top: 24px;
      padding-top: 24px;
      border-top: 1px solid #eee;
    }
    .chart-container h3 {
      font-size: 16px;
      color: #1a1a2e;
      margin-bottom: 16px;
    }
    .bar-chart {
      display: flex;
      align-items: flex-end;
      justify-content: space-around;
      height: 200px;
      padding: 0 20px;
    }
    .bar-chart-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      flex: 1;
      max-width: 80px;
    }
    .bar-chart-bar {
      width: 50px;
      border-radius: 8px 8px 0 0;
      transition: height 0.5s ease-out;
    }
    .bar-chart-label {
      margin-top: 8px;
      font-size: 14px;
      font-weight: 600;
      color: #1a1a2e;
    }
    .bar-chart-value {
      font-size: 11px;
      color: #666;
    }
    .legend {
      display: flex;
      justify-content: center;
      gap: 24px;
      margin-top: 16px;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: #666;
    }
    .legend-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
    .loading {
      text-align: center;
      padding: 40px;
      color: #666;
    }
  </style>
  ${previewScript}
</head>
<body>
  <div class="container">
    <div class="card">
      <div id="root"><div class="loading">Loading comparison...</div></div>
    </div>
  </div>
  <script>
    (function() {
      let rendered = false;

      function formatCurrency(num) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(num);
      }

      function render(data) {
        if (rendered || !data || !data.scenarios) return;
        rendered = true;

        const scenarios = data.scenarios;
        const maxMonthly = Math.max(...scenarios.map(s => s.monthlyPayment));
        const minMonthly = Math.min(...scenarios.map(s => s.monthlyPayment));
        const maxTotal = Math.max(...scenarios.map(s => s.totalCost));

        const scenariosHtml = scenarios.map((s, i) => {
          const barWidth = 50 + (s.monthlyPayment / maxMonthly) * 50;
          const hasPMI = s.downPaymentPercent < 20;
          const isBest = s.monthlyPayment === minMonthly;
          const savings = i > 0 ? scenarios[0].monthlyPayment - s.monthlyPayment : 0;

          return '<div class="scenario' + (isBest ? ' best' : '') + '">' +
            '<div class="down-percent">' + s.downPaymentPercent + '%</div>' +
            '<div class="bar-container">' +
              '<div class="bar ' + (hasPMI ? 'pmi' : 'no-pmi') + '" style="width:' + barWidth + '%">' +
                formatCurrency(s.downPayment) + ' down' +
              '</div>' +
            '</div>' +
            '<div class="monthly-info">' +
              '<div class="monthly-amount">' + formatCurrency(s.monthlyPayment) + '</div>' +
              '<div class="monthly-label">per month</div>' +
              (savings > 0 ? '<div class="savings">Save ' + formatCurrency(savings) + '/mo</div>' : '') +
            '</div>' +
          '</div>';
        }).join('');

        const barChartHtml = scenarios.map(s => {
          const barHeight = (s.totalCost / maxTotal) * 180;
          const hasPMI = s.downPaymentPercent < 20;
          return '<div class="bar-chart-item">' +
            '<div class="bar-chart-bar" style="height:' + barHeight + 'px; background: ' + (hasPMI ? '#ff6b6b' : '#11998e') + '"></div>' +
            '<div class="bar-chart-label">' + s.downPaymentPercent + '%</div>' +
            '<div class="bar-chart-value">' + formatCurrency(s.totalCost) + '</div>' +
          '</div>';
        }).join('');

        document.getElementById('root').innerHTML =
          '<div class="header">' +
            '<h1>Down Payment Comparison</h1>' +
            '<div class="subtitle">' + formatCurrency(data.homePrice) + ' home at ' + data.interestRate + '% for ' + data.loanTermYears + ' years</div>' +
          '</div>' +
          '<div class="scenarios">' + scenariosHtml + '</div>' +
          '<div class="chart-container">' +
            '<h3>Total Cost Comparison</h3>' +
            '<div class="bar-chart">' + barChartHtml + '</div>' +
            '<div class="legend">' +
              '<div class="legend-item"><span class="legend-dot" style="background:#ff6b6b"></span>Includes PMI</div>' +
              '<div class="legend-item"><span class="legend-dot" style="background:#11998e"></span>No PMI</div>' +
            '</div>' +
          '</div>';
      }

      function tryRender() {
        if (window.PREVIEW_DATA) { render(window.PREVIEW_DATA); return; }
        if (window.openai?.toolOutput) { render(window.openai.toolOutput); }
      }

      window.addEventListener('openai:set_globals', tryRender);

      const poll = setInterval(() => {
        if (window.openai?.toolOutput || window.PREVIEW_DATA) {
          tryRender();
          clearInterval(poll);
        }
      }, 100);
      setTimeout(() => clearInterval(poll), 10000);

      tryRender();
    })();
  </script>
</body>
</html>`;
}

function generateAmortizationChartHtml(previewData?: Record<string, unknown>): string {
  const previewScript = previewData
    ? `<script>window.PREVIEW_DATA = ${JSON.stringify(previewData)};</script>`
    : "";

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Amortization Schedule</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      min-height: 100vh;
      padding: 20px;
    }
    .container {
      max-width: 800px;
      margin: 0 auto;
    }
    .card {
      background: white;
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    .header {
      text-align: center;
      margin-bottom: 24px;
    }
    .header h1 {
      font-size: 24px;
      color: #1a1a2e;
      margin-bottom: 8px;
    }
    .header .subtitle {
      color: #666;
      font-size: 14px;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat {
      background: #f8f9ff;
      border-radius: 12px;
      padding: 16px;
      text-align: center;
    }
    .stat .value {
      font-size: 24px;
      font-weight: 700;
      color: #4facfe;
    }
    .stat .label {
      font-size: 12px;
      color: #666;
      margin-top: 4px;
    }
    .chart-container {
      position: relative;
      height: 300px;
      margin-bottom: 24px;
    }
    canvas {
      width: 100%;
      height: 100%;
    }
    .legend {
      display: flex;
      justify-content: center;
      gap: 32px;
      margin-bottom: 24px;
    }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
    }
    .legend-box {
      width: 16px;
      height: 16px;
      border-radius: 4px;
    }
    .table-container {
      max-height: 300px;
      overflow-y: auto;
      border-radius: 12px;
      border: 1px solid #eee;
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    th {
      background: #f8f9ff;
      padding: 12px 16px;
      text-align: left;
      font-size: 12px;
      font-weight: 600;
      color: #666;
      text-transform: uppercase;
      position: sticky;
      top: 0;
    }
    td {
      padding: 12px 16px;
      border-top: 1px solid #eee;
      font-size: 14px;
    }
    tr:hover {
      background: #f8f9ff;
    }
    .loading {
      text-align: center;
      padding: 40px;
      color: #666;
    }
  </style>
  ${previewScript}
</head>
<body>
  <div class="container">
    <div class="card">
      <div id="root"><div class="loading">Loading amortization schedule...</div></div>
    </div>
  </div>
  <script>
    (function() {
      let rendered = false;

      function formatCurrency(num) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(num);
      }

      function drawChart(canvas, schedule, loanAmount) {
        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);

        const width = rect.width;
        const height = rect.height;
        const padding = { top: 20, right: 20, bottom: 40, left: 60 };
        const chartWidth = width - padding.left - padding.right;
        const chartHeight = height - padding.top - padding.bottom;

        // Find max values
        const maxValue = loanAmount;
        const maxYear = schedule[schedule.length - 1].year;

        // Draw grid
        ctx.strokeStyle = '#eee';
        ctx.lineWidth = 1;
        for (let i = 0; i <= 5; i++) {
          const y = padding.top + (chartHeight / 5) * i;
          ctx.beginPath();
          ctx.moveTo(padding.left, y);
          ctx.lineTo(width - padding.right, y);
          ctx.stroke();

          // Y-axis labels
          ctx.fillStyle = '#999';
          ctx.font = '11px -apple-system, sans-serif';
          ctx.textAlign = 'right';
          const value = maxValue - (maxValue / 5) * i;
          ctx.fillText(formatCurrency(value), padding.left - 8, y + 4);
        }

        // X-axis labels
        ctx.textAlign = 'center';
        const yearStep = Math.ceil(maxYear / 6);
        for (let year = 0; year <= maxYear; year += yearStep) {
          const x = padding.left + (year / maxYear) * chartWidth;
          ctx.fillText('Year ' + year, x, height - 10);
        }

        // Draw stacked area chart
        // First: Principal (bottom)
        ctx.beginPath();
        ctx.moveTo(padding.left, padding.top + chartHeight);

        schedule.forEach((entry, i) => {
          const x = padding.left + (entry.year / maxYear) * chartWidth;
          const principalHeight = (entry.totalPrincipalPaid / maxValue) * chartHeight;
          ctx.lineTo(x, padding.top + chartHeight - principalHeight);
        });

        ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
        ctx.closePath();
        ctx.fillStyle = 'rgba(79, 172, 254, 0.8)';
        ctx.fill();

        // Second: Interest (top)
        ctx.beginPath();
        ctx.moveTo(padding.left, padding.top + chartHeight);

        schedule.forEach((entry, i) => {
          const x = padding.left + (entry.year / maxYear) * chartWidth;
          const totalHeight = ((entry.totalPrincipalPaid + entry.totalInterestPaid) / maxValue) * chartHeight;
          ctx.lineTo(x, padding.top + chartHeight - totalHeight);
        });

        // Close from right side down
        for (let i = schedule.length - 1; i >= 0; i--) {
          const entry = schedule[i];
          const x = padding.left + (entry.year / maxYear) * chartWidth;
          const principalHeight = (entry.totalPrincipalPaid / maxValue) * chartHeight;
          ctx.lineTo(x, padding.top + chartHeight - principalHeight);
        }

        ctx.closePath();
        ctx.fillStyle = 'rgba(255, 107, 107, 0.8)';
        ctx.fill();

        // Draw balance line
        ctx.beginPath();
        ctx.strokeStyle = '#1a1a2e';
        ctx.lineWidth = 3;
        schedule.forEach((entry, i) => {
          const x = padding.left + (entry.year / maxYear) * chartWidth;
          const y = padding.top + ((maxValue - entry.balance) / maxValue) * chartHeight;
          if (i === 0) {
            ctx.moveTo(padding.left, padding.top);
          }
          ctx.lineTo(x, padding.top + (entry.balance / maxValue) * chartHeight);
        });
        ctx.stroke();
      }

      function render(data) {
        if (rendered || !data || !data.schedule) return;
        rendered = true;

        const schedule = data.schedule;
        const lastEntry = schedule[schedule.length - 1];
        const totalPaid = lastEntry.totalPrincipalPaid + lastEntry.totalInterestPaid;

        const tableRows = schedule.map(entry =>
          '<tr>' +
            '<td>Year ' + entry.year + '</td>' +
            '<td>' + formatCurrency(entry.totalPrincipalPaid) + '</td>' +
            '<td>' + formatCurrency(entry.totalInterestPaid) + '</td>' +
            '<td>' + formatCurrency(entry.balance) + '</td>' +
          '</tr>'
        ).join('');

        document.getElementById('root').innerHTML =
          '<div class="header">' +
            '<h1>Amortization Schedule</h1>' +
            '<div class="subtitle">' + formatCurrency(data.loanAmount) + ' loan at ' + data.interestRate + '% over ' + data.loanTermYears + ' years</div>' +
          '</div>' +
          '<div class="stats">' +
            '<div class="stat"><div class="value">' + formatCurrency(data.loanAmount) + '</div><div class="label">Loan Amount</div></div>' +
            '<div class="stat"><div class="value">' + formatCurrency(lastEntry.totalInterestPaid) + '</div><div class="label">Total Interest</div></div>' +
            '<div class="stat"><div class="value">' + formatCurrency(totalPaid) + '</div><div class="label">Total Paid</div></div>' +
          '</div>' +
          '<div class="chart-container"><canvas id="chart"></canvas></div>' +
          '<div class="legend">' +
            '<div class="legend-item"><div class="legend-box" style="background:rgba(79,172,254,0.8)"></div>Principal Paid</div>' +
            '<div class="legend-item"><div class="legend-box" style="background:rgba(255,107,107,0.8)"></div>Interest Paid</div>' +
            '<div class="legend-item"><div class="legend-box" style="background:#1a1a2e"></div>Remaining Balance</div>' +
          '</div>' +
          '<div class="table-container">' +
            '<table>' +
              '<thead><tr><th>Year</th><th>Principal Paid</th><th>Interest Paid</th><th>Balance</th></tr></thead>' +
              '<tbody>' + tableRows + '</tbody>' +
            '</table>' +
          '</div>';

        // Draw chart after DOM update
        setTimeout(() => {
          const canvas = document.getElementById('chart');
          if (canvas) drawChart(canvas, schedule, data.loanAmount);
        }, 0);
      }

      function tryRender() {
        if (window.PREVIEW_DATA) { render(window.PREVIEW_DATA); return; }
        if (window.openai?.toolOutput) { render(window.openai.toolOutput); }
      }

      window.addEventListener('openai:set_globals', tryRender);

      const poll = setInterval(() => {
        if (window.openai?.toolOutput || window.PREVIEW_DATA) {
          tryRender();
          clearInterval(poll);
        }
      }, 100);
      setTimeout(() => clearInterval(poll), 10000);

      tryRender();
    })();
  </script>
</body>
</html>`;
}

function generateWidgetHtml(widgetId: string, previewData?: Record<string, unknown>): string {
  switch (widgetId) {
    case "mortgage-summary":
      return generateMortgageSummaryHtml(previewData);
    case "down-payment-comparison":
      return generateDownPaymentComparisonHtml(previewData);
    case "amortization-chart":
      return generateAmortizationChartHtml(previewData);
    default:
      return `<html><body>Widget not found: ${widgetId}</body></html>`;
  }
}

// ============================================================================
// TOOL DEFINITIONS
// ============================================================================

interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: {
    type: "object";
    properties: Record<string, unknown>;
    required: string[];
  };
  annotations: {
    title: string;
    readOnlyHint: boolean;
    destructiveHint: boolean;
    openWorldHint: boolean;
  };
  widgetId?: string;
  execute: (args: Record<string, unknown>) => unknown;
}

const tools: ToolDefinition[] = [
  {
    name: "calculate_mortgage",
    description: "Calculate monthly mortgage payment for a specific scenario. Includes principal, interest, property tax, insurance, and PMI (if applicable). Use this when the user asks about a single mortgage scenario.",
    inputSchema: {
      type: "object" as const,
      properties: {
        homePrice: {
          type: "number",
          description: "The total price of the home in dollars",
        },
        downPaymentPercent: {
          type: "number",
          description: "Down payment as a percentage (e.g., 20 for 20%)",
        },
        interestRate: {
          type: "number",
          description: "Annual interest rate as a percentage (e.g., 6.5 for 6.5%)",
        },
        loanTermYears: {
          type: "number",
          description: "Loan term in years (typically 15, 20, or 30)",
          default: 30,
        },
        propertyTaxRate: {
          type: "number",
          description: "Annual property tax rate as a percentage (default 1.2%)",
          default: 1.2,
        },
        homeInsuranceAnnual: {
          type: "number",
          description: "Annual home insurance cost in dollars (default $1200)",
          default: 1200,
        },
      },
      required: ["homePrice", "downPaymentPercent", "interestRate"],
    },
    annotations: {
      title: "Calculate Mortgage",
      readOnlyHint: true,
      destructiveHint: false,
      openWorldHint: false,
    },
    widgetId: "mortgage-summary",
    execute: (args) => {
      return calculateMortgage({
        homePrice: args.homePrice as number,
        downPaymentPercent: args.downPaymentPercent as number,
        interestRate: args.interestRate as number,
        loanTermYears: (args.loanTermYears as number) || 30,
        propertyTaxRate: args.propertyTaxRate as number,
        homeInsuranceAnnual: args.homeInsuranceAnnual as number,
      });
    },
  },
  {
    name: "compare_down_payments",
    description: "Compare different down payment scenarios side by side. Shows how different down payment percentages affect monthly payments, PMI, and total cost. Use this when the user wants to see multiple options.",
    inputSchema: {
      type: "object" as const,
      properties: {
        homePrice: {
          type: "number",
          description: "The total price of the home in dollars",
        },
        downPaymentPercents: {
          type: "array",
          items: { type: "number" },
          description: "Array of down payment percentages to compare (e.g., [5, 10, 15, 20])",
        },
        interestRate: {
          type: "number",
          description: "Annual interest rate as a percentage",
        },
        loanTermYears: {
          type: "number",
          description: "Loan term in years (default 30)",
          default: 30,
        },
      },
      required: ["homePrice", "downPaymentPercents", "interestRate"],
    },
    annotations: {
      title: "Compare Down Payments",
      readOnlyHint: true,
      destructiveHint: false,
      openWorldHint: false,
    },
    widgetId: "down-payment-comparison",
    execute: (args) => {
      const percents = args.downPaymentPercents as number[];
      const scenarios = percents.map((pct) => {
        const result = calculateMortgage({
          homePrice: args.homePrice as number,
          downPaymentPercent: pct,
          interestRate: args.interestRate as number,
          loanTermYears: (args.loanTermYears as number) || 30,
        });
        return {
          downPaymentPercent: pct,
          downPayment: result.downPayment,
          loanAmount: result.loanAmount,
          monthlyPayment: result.totalMonthlyPayment,
          monthlyPMI: result.monthlyPMI,
          totalCost: result.totalCost,
          totalInterestPaid: result.totalInterestPaid,
        };
      });

      return {
        homePrice: args.homePrice,
        interestRate: args.interestRate,
        loanTermYears: (args.loanTermYears as number) || 30,
        scenarios,
      };
    },
  },
  {
    name: "show_amortization",
    description: "Display the loan amortization schedule over time with a graphical chart. Shows how principal and interest payments change throughout the loan term, and how the balance decreases over time.",
    inputSchema: {
      type: "object" as const,
      properties: {
        homePrice: {
          type: "number",
          description: "The total price of the home in dollars",
        },
        downPaymentPercent: {
          type: "number",
          description: "Down payment as a percentage",
        },
        interestRate: {
          type: "number",
          description: "Annual interest rate as a percentage",
        },
        loanTermYears: {
          type: "number",
          description: "Loan term in years (default 30)",
          default: 30,
        },
        granularity: {
          type: "string",
          enum: ["yearly", "monthly"],
          description: "Show yearly or monthly breakdown (default yearly)",
          default: "yearly",
        },
      },
      required: ["homePrice", "downPaymentPercent", "interestRate"],
    },
    annotations: {
      title: "Show Amortization",
      readOnlyHint: true,
      destructiveHint: false,
      openWorldHint: false,
    },
    widgetId: "amortization-chart",
    execute: (args) => {
      const input: MortgageInput = {
        homePrice: args.homePrice as number,
        downPaymentPercent: args.downPaymentPercent as number,
        interestRate: args.interestRate as number,
        loanTermYears: (args.loanTermYears as number) || 30,
      };

      const schedule = generateAmortizationSchedule(
        input,
        (args.granularity as "yearly" | "monthly") || "yearly"
      );

      const result = calculateMortgage(input);

      return {
        homePrice: input.homePrice,
        downPaymentPercent: input.downPaymentPercent,
        loanAmount: result.loanAmount,
        interestRate: input.interestRate,
        loanTermYears: input.loanTermYears,
        monthlyPayment: result.monthlyPrincipalInterest,
        schedule,
      };
    },
  },
];

// ============================================================================
// MCP SERVER FACTORY
// ============================================================================

function createServer(): Server {
  const server = new Server(
    { name: "mortgage-calculator", version: "1.0.0" },
    { capabilities: { tools: {}, resources: {} } }
  );

  // ListTools handler
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    log("ListTools request");
    return {
      tools: tools.map((tool) => {
        const widget = tool.widgetId ? WIDGETS_BY_ID.get(tool.widgetId) : null;
        return {
          name: tool.name,
          description: tool.description,
          inputSchema: tool.inputSchema,
          annotations: tool.annotations,
          ...(widget && {
            _meta: {
              "openai/outputTemplate": widget.templateUri,
              "openai/widgetAccessible": true,
              "openai/resultCanProduceWidget": true,
              "openai/toolInvocation/invoking": widget.invoking,
            },
          }),
        };
      }),
    };
  });

  // CallTool handler
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    log(`CallTool: ${name}`, args);

    const tool = tools.find((t) => t.name === name);
    if (!tool) throw new Error(`Unknown tool: ${name}`);

    try {
      const result = tool.execute(args || {});
      const widget = tool.widgetId ? WIDGETS_BY_ID.get(tool.widgetId) : null;

      if (widget) {
        return {
          content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
          structuredContent: result,
          _meta: {
            "openai/outputTemplate": widget.templateUri,
            "openai/toolInvocation/invoked": widget.invoked,
          },
        };
      }

      return { content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }] };
    } catch (error) {
      return {
        content: [{ type: "text" as const, text: `Error: ${error instanceof Error ? error.message : "Unknown error"}` }],
        isError: true,
      };
    }
  });

  // ListResources handler
  server.setRequestHandler(ListResourcesRequestSchema, async () => {
    return {
      resources: widgets.map((w) => ({
        uri: w.templateUri,
        name: w.name,
        description: w.description,
        mimeType: "text/html+skybridge",
      })),
    };
  });

  // ReadResource handler
  server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    const { uri } = request.params;
    const widget = WIDGETS_BY_URI.get(uri);
    if (!widget) throw new Error(`Unknown resource: ${uri}`);

    return {
      contents: [{ uri, mimeType: "text/html+skybridge", text: generateWidgetHtml(widget.id) }],
      _meta: {
        "openai/serialization": "markdown-encoded-html",
        "openai/csp": { script_domains: ["'unsafe-inline'"], connect_domains: [WIDGET_DOMAIN] },
      },
    };
  });

  return server;
}

// ============================================================================
// EXPRESS APP WITH SESSION MANAGEMENT
// ============================================================================

const app = express();
app.use(express.json());

const transports = new Map<string, StreamableHTTPServerTransport>();

// Health endpoint
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    service: "mortgage-calculator",
    widgets: widgets.length,
    tools: tools.length,
  });
});

// Widget preview index
app.get("/preview", (req, res) => {
  res.send(`<!DOCTYPE html>
<html>
<head>
  <title>Mortgage Calculator - Widget Preview</title>
  <style>
    body { font-family: -apple-system, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }
    h1 { color: #1a1a2e; }
    .widget-list { display: grid; gap: 16px; }
    .widget-card {
      border: 1px solid #eee;
      border-radius: 12px;
      padding: 20px;
      transition: box-shadow 0.2s;
    }
    .widget-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .widget-card h2 { margin: 0 0 8px; color: #667eea; }
    .widget-card p { margin: 0 0 16px; color: #666; }
    .widget-card a {
      display: inline-block;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 8px 16px;
      border-radius: 8px;
      text-decoration: none;
    }
    .widget-card a:hover { opacity: 0.9; }
  </style>
</head>
<body>
  <h1>🏠 Mortgage Calculator</h1>
  <p>Preview the widgets with mock data:</p>
  <div class="widget-list">
    ${widgets.map(w => `
      <div class="widget-card">
        <h2>${w.name}</h2>
        <p>${w.description}</p>
        <a href="/preview/${w.id}">Preview Widget →</a>
      </div>
    `).join('')}
  </div>
</body>
</html>`);
});

// Widget preview with mock data
app.get("/preview/:widgetId", (req, res) => {
  const widget = WIDGETS_BY_ID.get(req.params.widgetId);
  if (!widget) {
    res.status(404).send("Widget not found");
    return;
  }
  res.setHeader("Content-Type", "text/html");
  res.send(generateWidgetHtml(widget.id, widget.mockData));
});

// MCP endpoint with session management
app.all("/mcp", async (req, res) => {
  log("MCP request:", req.method, req.headers["mcp-session-id"] || "no-session");

  let sessionId = req.headers["mcp-session-id"] as string | undefined;
  let transport = sessionId ? transports.get(sessionId) : undefined;

  const isInitialize =
    req.body?.method === "initialize" ||
    (Array.isArray(req.body) &&
      req.body.some((m: JSONRPCMessage) => "method" in m && m.method === "initialize"));

  if (isInitialize || !sessionId || !transport) {
    sessionId = randomUUID();
    log(`New session: ${sessionId}`);

    transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => sessionId!,
      onsessioninitialized: (id) => log(`Session initialized: ${id}`),
    });

    transports.set(sessionId, transport);
    const server = createServer();

    res.on("close", () => log(`Connection closed: ${sessionId}`));
    transport.onclose = () => {
      transports.delete(sessionId!);
      server.close();
    };

    await server.connect(transport);
  }

  await transport.handleRequest(req, res, req.body);
});

app.delete("/mcp", async (req, res) => {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;
  if (sessionId && transports.has(sessionId)) {
    await transports.get(sessionId)!.handleRequest(req, res, req.body);
  } else {
    res.status(404).json({ error: "Session not found" });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`\n🏠 Mortgage Calculator MCP Server`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
  console.log(`  MCP:     http://localhost:${PORT}/mcp`);
  console.log(`  Health:  http://localhost:${PORT}/health`);
  console.log(`  Preview: http://localhost:${PORT}/preview`);
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);
});
