'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useAuthStore } from '@/store/auth';
import apiClient from '@/lib/api';
import {
  CreditCard,
  Download,
  Settings,
  AlertCircle,
  Check,
  Calendar,
  Zap,
  Trash2,
} from 'lucide-react';

interface Subscription {
  id: string;
  status: string;
  tier: string;
  billing_cycle: string;
  current_period_start: string;
  current_period_end: string;
  trial_end?: string;
  created_at: string;
}

interface Invoice {
  id: string;
  invoice_number: string;
  amount_total: number;
  status: string;
  date_created: string;
  date_paid?: string;
  pdf_url?: string;
}

interface PaymentMethod {
  id: string;
  type: string;
  card_brand?: string;
  card_last4?: string;
  card_exp_month?: number;
  card_exp_year?: number;
  is_default: boolean;
}

export const BillingPortal: React.FC = () => {
  const { user } = useAuthStore();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [cancelingSubscription, setCancelingSubscription] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [subData, invoicesData, methodsData] = await Promise.all([
          apiClient.get('/api/payments/subscription'),
          apiClient.get('/api/payments/invoices'),
          apiClient.get('/api/payments/payment-methods'),
        ]);

        setSubscription(subData);
        setInvoices(invoicesData);
        setPaymentMethods(methodsData.payment_methods || []);
      } catch (err) {
        console.error('Failed to fetch billing data:', err);
        setError('Failed to load billing information');
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchData();
    }
  }, [user]);

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure? Your subscription will be canceled at the end of the billing period.')) {
      return;
    }

    try {
      setCancelingSubscription(true);
      await apiClient.post('/api/payments/subscription/cancel');
      setSubscription((prev) =>
        prev ? { ...prev, status: 'canceled' } : null
      );
    } catch (err) {
      console.error('Failed to cancel subscription:', err);
      setError('Failed to cancel subscription');
    } finally {
      setCancelingSubscription(false);
    }
  };

  const handleOpenBillingPortal = async () => {
    try {
      const response = await apiClient.post('/api/payments/billing-portal');
      window.location.href = response.url;
    } catch (err) {
      console.error('Failed to open billing portal:', err);
      setError('Failed to open billing portal');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatAmount = (cents: number) => {
    return `$${(cents / 100).toFixed(2)}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-slate-400">Loading billing information...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-900/20 rounded-lg border border-red-700 text-red-400">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* Current Subscription */}
      <div className="rounded-lg bg-slate-800/50 border border-slate-700 p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <Zap className="w-5 h-5 text-blue-400" />
              Current Plan
            </h2>
          </div>
          <button
            onClick={handleOpenBillingPortal}
            className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-100 transition"
          >
            <Settings className="w-4 h-4" />
            Manage
          </button>
        </div>

        {subscription ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-400">Plan</p>
                <p className="text-lg font-semibold text-slate-100 capitalize">
                  {subscription.tier}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Status</p>
                <div className="flex items-center gap-2 mt-1">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      subscription.status === 'active'
                        ? 'bg-green-500'
                        : subscription.status === 'canceled'
                        ? 'bg-red-500'
                        : 'bg-yellow-500'
                    }`}
                  />
                  <span className="text-slate-100 capitalize">
                    {subscription.status}
                  </span>
                </div>
              </div>
              <div>
                <p className="text-sm text-slate-400">Billing Cycle</p>
                <p className="text-slate-100 capitalize">
                  {subscription.billing_cycle}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-400">Next Billing</p>
                <p className="text-slate-100">
                  {formatDate(subscription.current_period_end)}
                </p>
              </div>
            </div>

            {subscription.trial_end && (
              <div className="p-3 bg-blue-900/20 rounded-lg border border-blue-700">
                <p className="text-sm text-blue-300">
                  Trial ends {formatDate(subscription.trial_end)}
                </p>
              </div>
            )}

            {subscription.status === 'active' && (
              <button
                onClick={handleCancelSubscription}
                disabled={cancelingSubscription}
                className="w-full mt-4 py-2 px-4 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition disabled:opacity-50"
              >
                {cancelingSubscription
                  ? 'Canceling...'
                  : 'Cancel Subscription'}
              </button>
            )}
          </div>
        ) : (
          <p className="text-slate-300">No active subscription</p>
        )}
      </div>

      {/* Invoices */}
      <div className="rounded-lg bg-slate-800/50 border border-slate-700 p-6">
        <h2 className="text-xl font-bold text-slate-100 mb-6 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-blue-400" />
          Invoices
        </h2>

        {invoices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">
                    Invoice
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">
                    Date
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">
                    Amount
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">
                    Status
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-slate-400">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => (
                  <tr
                    key={invoice.id}
                    className="border-b border-slate-700 hover:bg-slate-700/20 transition"
                  >
                    <td className="py-3 px-4 text-slate-100">
                      #{invoice.invoice_number}
                    </td>
                    <td className="py-3 px-4 text-slate-300">
                      {formatDate(invoice.date_created)}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-100">
                      {formatAmount(invoice.amount_total)}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          invoice.status === 'paid'
                            ? 'bg-green-900/30 text-green-400'
                            : invoice.status === 'open'
                            ? 'bg-yellow-900/30 text-yellow-400'
                            : 'bg-gray-900/30 text-gray-400'
                        }`}
                      >
                        {invoice.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      {invoice.pdf_url && (
                        <a
                          href={invoice.pdf_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 transition"
                        >
                          <Download className="w-4 h-4" />
                          <span className="text-sm">PDF</span>
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-slate-400">No invoices yet</p>
        )}
      </div>

      {/* Payment Methods */}
      <div className="rounded-lg bg-slate-800/50 border border-slate-700 p-6">
        <div className="flex items-start justify-between mb-6">
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-blue-400" />
            Payment Methods
          </h2>
          <button
            onClick={handleOpenBillingPortal}
            className="text-sm text-blue-400 hover:text-blue-300 transition"
          >
            Add Payment Method
          </button>
        </div>

        {paymentMethods.length > 0 ? (
          <div className="space-y-3">
            {paymentMethods.map((method) => (
              <div
                key={method.id}
                className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg border border-slate-600"
              >
                <div className="flex items-center gap-4">
                  <CreditCard className="w-5 h-5 text-slate-400" />
                  <div>
                    <div className="font-medium text-slate-100 capitalize">
                      {method.card_brand} •••• {method.card_last4}
                    </div>
                    <div className="text-sm text-slate-400">
                      Expires {method.card_exp_month}/{method.card_exp_year}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {method.is_default && (
                    <span className="flex items-center gap-1 text-xs font-medium text-green-400 bg-green-900/20 px-2 py-1 rounded">
                      <Check className="w-3 h-3" />
                      Default
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-slate-400">No payment methods added</p>
        )}
      </div>
    </div>
  );
};
