'use client';

import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/auth';
import apiClient from '@/lib/api';
import {
  CheckCircle,
  AlertCircle,
  ArrowRight,
  Loader,
  Clock,
  TrendingUp,
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

interface SubscriptionManagerProps {
  onUpgradeClick?: (plan: PricingPlan, cycle: 'monthly' | 'annual') => void;
}

export const SubscriptionManager: React.FC<SubscriptionManagerProps> = ({
  onUpgradeClick,
}) => {
  const { user } = useAuthStore();
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCycle, setSelectedCycle] = useState<'monthly' | 'annual'>(
    'monthly'
  );
  const [upgradingTo, setUpgradingTo] = useState<string | null>(null);

  const tierOrder = ['free', 'starter', 'professional', 'enterprise'];

  useEffect(() => {
    fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [subData, pricingData] = await Promise.all([
        apiClient.get('/api/payments/subscription'),
        apiClient.get('/api/payments/pricing'),
      ]);

      setSubscription(subData);
      setPlans(pricingData.plans || []);
    } catch (err) {
      console.error('Failed to fetch subscription data:', err);
      setError('Failed to load subscription information');
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (plan: PricingPlan) => {
    if (onUpgradeClick) {
      onUpgradeClick(plan, selectedCycle);
    } else {
      try {
        setUpgradingTo(plan.id);
        const checkoutSession = await apiClient.post('/api/payments/checkout', {
          plan_id: plan.id,
          billing_cycle: selectedCycle,
        });
        window.location.href = checkoutSession.url;
      } catch (err) {
        console.error('Failed to create checkout session:', err);
        setError('Failed to initiate upgrade');
      } finally {
        setUpgradingTo(null);
      }
    }
  };

  const canUpgrade = (plan: PricingPlan): boolean => {
    if (!subscription || subscription.tier === 'free') return true;
    return (
      tierOrder.indexOf(plan.tier.toLowerCase()) >
      tierOrder.indexOf(subscription.tier.toLowerCase())
    );
  };

  const formatPrice = (cents?: number) => {
    if (!cents) return 'Free';
    return `$${(cents / 100).toFixed(2)}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader className="w-6 h-6 animate-spin text-blue-400" />
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

      {/* Current Subscription Summary */}
      {subscription && (
        <div className="rounded-lg bg-gradient-to-r from-blue-900/30 to-slate-900/30 border border-blue-700 p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold text-blue-100 mb-2 capitalize">
                {subscription.tier} Plan
              </h2>
              <p className="text-slate-300 flex items-center gap-2">
                <span
                  className={`w-2 h-2 rounded-full ${
                    subscription.status === 'active'
                      ? 'bg-green-500'
                      : 'bg-yellow-500'
                  }`}
                />
                {subscription.status === 'active'
                  ? 'Active'
                  : 'Inactive'}{' '}
                • {subscription.billing_cycle} billing
              </p>
            </div>
            {subscription.status === 'active' && (
              <CheckCircle className="w-8 h-8 text-green-400" />
            )}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-700 text-sm text-slate-300 space-y-1">
            {subscription.trial_end ? (
              <p className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Trial ends: {formatDate(subscription.trial_end)}
              </p>
            ) : (
              <p className="flex items-center gap-2">
                <TrendingUp className="w-4 h-4" />
                Renews on: {formatDate(subscription.current_period_end)}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Billing Cycle Selector */}
      <div className="flex gap-4 items-center">
        <div className="flex bg-slate-800 rounded-lg p-1">
          <button
            onClick={() => setSelectedCycle('monthly')}
            className={`px-4 py-2 rounded transition ${
              selectedCycle === 'monthly'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setSelectedCycle('annual')}
            className={`px-4 py-2 rounded transition ${
              selectedCycle === 'annual'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            Annual
            <span className="ml-2 text-xs bg-green-900/40 text-green-400 px-2 py-1 rounded">
              Save 20%
            </span>
          </button>
        </div>
      </div>

      {/* Available Plans */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {plans.map((plan) => {
          const isCurrentPlan = subscription?.tier.toLowerCase() === plan.tier.toLowerCase();
          const price =
            selectedCycle === 'monthly'
              ? plan.price_monthly
              : plan.price_annual;
          const canUpgradeTo = canUpgrade(plan);

          return (
            <div
              key={plan.id}
              className={`rounded-lg border transition ${
                isCurrentPlan
                  ? 'bg-blue-900/20 border-blue-600'
                  : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
              }`}
            >
              <div className="p-6 space-y-6">
                {/* Plan Header */}
                <div>
                  <h3 className="text-lg font-bold text-slate-100 capitalize">
                    {plan.name}
                  </h3>
                  <p className="text-sm text-slate-400 mt-1">
                    {plan.description}
                  </p>
                </div>

                {/* Pricing */}
                <div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-slate-100">
                      {formatPrice(price)}
                    </span>
                    {price && (
                      <span className="text-slate-400">
                        /{selectedCycle === 'monthly' ? 'mo' : 'yr'}
                      </span>
                    )}
                  </div>
                </div>

                {/* Features */}
                <ul className="space-y-2">
                  {plan.features.slice(0, 3).map((feature, idx) => (
                    <li
                      key={idx}
                      className="text-sm text-slate-300 flex items-start gap-2"
                    >
                      <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                  {plan.features.length > 3 && (
                    <li className="text-sm text-slate-400">
                      +{plan.features.length - 3} more features
                    </li>
                  )}
                </ul>

                {/* Limits */}
                {Object.entries(plan.limits).length > 0 && (
                  <div className="pt-4 border-t border-slate-700 space-y-2">
                    {Object.entries(plan.limits)
                      .slice(0, 2)
                      .map(([key, value]) => (
                        <div
                          key={key}
                          className="text-xs text-slate-400 flex justify-between"
                        >
                          <span className="capitalize">{key.replace(/_/g, ' ')}:</span>
                          <span className="font-medium text-slate-300">
                            {value}
                          </span>
                        </div>
                      ))}
                  </div>
                )}

                {/* Action Button */}
                <button
                  onClick={() => handleUpgrade(plan)}
                  disabled={!canUpgradeTo || upgradingTo === plan.id}
                  className={`w-full py-2 px-4 rounded-lg font-medium transition flex items-center justify-center gap-2 ${
                    isCurrentPlan
                      ? 'bg-blue-600/20 text-blue-300 border border-blue-600 cursor-default'
                      : canUpgradeTo
                      ? 'bg-blue-600 hover:bg-blue-700 text-white'
                      : 'bg-slate-700 text-slate-500 cursor-not-allowed'
                  }`}
                >
                  {isCurrentPlan ? (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      Current Plan
                    </>
                  ) : upgradingTo === plan.id ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      Processing...
                    </>
                  ) : canUpgradeTo ? (
                    <>
                      Upgrade
                      <ArrowRight className="w-4 h-4" />
                    </>
                  ) : (
                    'Contact Support'
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
