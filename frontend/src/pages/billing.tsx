'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { BillingPortal } from '@/components/BillingPortal';
import { SubscriptionManager } from '@/components/SubscriptionManager';
import { PaymentMethods } from '@/components/PaymentMethods';
import {
  CreditCard,
  Settings,
  TrendingUp,
  LogOut,
  AlertCircle,
} from 'lucide-react';

type TabType = 'overview' | 'plans' | 'payment-methods';

interface PricingPlan {
  id: string;
  name: string;
  tier: string;
  price_monthly?: number;
  price_annual?: number;
  features: string[];
  description: string;
  limits: Record<string, number | string>;
}

export default function BillingPage() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [showAddPaymentModal, setShowAddPaymentModal] = useState(false);

  const handleLogout = async () => {
    logout();
    router.push('/');
  };

  const handleUpgradeClick = (plan: PricingPlan, cycle: 'monthly' | 'annual') => {
    // This callback can be used to handle upgrade logic
    // For now, the SubscriptionManager handles it directly
  };

  const handleAddPaymentMethod = () => {
    // Redirect to Stripe self-service portal
    setShowAddPaymentModal(true);
  };

  const tabs: Array<{ id: TabType; label: string; icon: React.ReactNode }> = [
    { id: 'overview', label: 'Overview', icon: <Settings className="w-4 h-4" /> },
    {
      id: 'plans',
      label: 'Plans & Pricing',
      icon: <TrendingUp className="w-4 h-4" />,
    },
    {
      id: 'payment-methods',
      label: 'Payment Methods',
      icon: <CreditCard className="w-4 h-4" />,
    },
  ];

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-slate-100 mb-2">
            Not Authenticated
          </h1>
          <p className="text-slate-400 mb-6">
            Please log in to access billing information.
          </p>
          <button
            onClick={() => router.push('/login')}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white transition"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800/50 border-b border-slate-700 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-100">Billing & Subscription</h1>
            <p className="text-slate-400 text-sm mt-1">
              Manage your account, subscription, and payment methods
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 text-slate-400 hover:text-slate-300 hover:bg-slate-700/50 rounded-lg transition"
            title="Log out"
          >
            <LogOut className="w-4 h-4" />
            <span className="hidden sm:inline text-sm">Logout</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tab Navigation */}
        <div className="flex gap-2 mb-8 border-b border-slate-700 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 font-medium transition whitespace-nowrap border-b-2 ${
                activeTab === tab.id
                  ? 'text-blue-400 border-blue-400'
                  : 'text-slate-400 border-transparent hover:text-slate-300'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="rounded-lg bg-slate-800/30">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {/* Quick Stats */}
                <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">
                    Account Status
                  </h3>
                  <p className="text-2xl font-bold text-green-400">Active</p>
                </div>

                <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">
                    Member Since
                  </h3>
                  <p className="text-lg font-bold text-slate-100">
                    {user?.created_at
                      ? new Date(user.created_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })
                      : 'N/A'}
                  </p>
                </div>

                <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
                  <h3 className="text-sm font-medium text-slate-400 mb-2">
                    Email
                  </h3>
                  <p className="text-sm font-mono text-slate-200 break-all">
                    {user?.email}
                  </p>
                </div>
              </div>

              {/* Billing Portal */}
              <BillingPortal />
            </div>
          )}

          {/* Plans & Pricing Tab */}
          {activeTab === 'plans' && (
            <div className="p-6">
              <SubscriptionManager onUpgradeClick={handleUpgradeClick} />
            </div>
          )}

          {/* Payment Methods Tab */}
          {activeTab === 'payment-methods' && (
            <div className="p-6">
              <PaymentMethods onAddNew={handleAddPaymentMethod} editable={true} />
            </div>
          )}
        </div>

        {/* Support Footer */}
        <div className="mt-12 p-6 bg-blue-900/20 rounded-lg border border-blue-700">
          <h3 className="font-medium text-blue-100 mb-2">Need Help?</h3>
          <p className="text-sm text-blue-200 mb-4">
            Have questions about your subscription or billing? Our support team is here
            to help.
          </p>
          <div className="flex gap-4">
            <a
              href="mailto:support@omnidev.ai"
              className="text-sm text-blue-400 hover:text-blue-300 transition"
            >
              Contact Support
            </a>
            <a
              href="/docs/billing"
              className="text-sm text-blue-400 hover:text-blue-300 transition"
            >
              View Docs
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
