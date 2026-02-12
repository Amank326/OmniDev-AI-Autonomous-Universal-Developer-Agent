'use client';

import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/js';
import { EmbeddedCheckoutProvider, EmbeddedCheckout } from '@stripe/react-stripe-js';
import { useAuth } from '@/hooks/useAuth';
import { useAuthStore } from '@/store/auth';
import apiClient from '@/lib/api';
import { CreditCard, AlertCircle, CheckCircle } from 'lucide-react';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

interface PricingPlan {
  id: string;
  tier: string;
  name: string;
  price_monthly: number;
  price_annual?: number;
  trial_days: number;
  features: string[];
  max_projects?: number;
  storage_gb: number;
}

interface CheckoutProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
}

export const PricingCards: React.FC<{ onSelectPlan?: (tier: string, cycle: string) => void }> = ({
  onSelectPlan,
}) => {
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const data = await apiClient.get('/api/payments/pricing');
        setPlans(data);
      } catch (error) {
        console.error('Failed to fetch pricing plans:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-slate-400">Loading pricing plans...</div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {plans.map((plan) => (
        <div
          key={plan.id}
          className="relative rounded-lg bg-slate-800/50 border border-slate-700 p-6 hover:border-slate-600 transition"
        >
          {/* Popular Badge */}
          {plan.tier === 'professional' && (
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-blue-600 rounded-full text-xs font-semibold">
              Most Popular
            </div>
          )}

          {/* Plan Name & Price */}
          <div className="mb-4">
            <h3 className="text-lg font-bold text-slate-100">{plan.name}</h3>
            <div className="mt-2 flex items-baseline gap-1">
              <span className="text-3xl font-bold text-slate-100">
                ${plan.price_monthly}
              </span>
              <span className="text-slate-400">/month</span>
            </div>
            {plan.price_annual && (
              <div className="mt-1 text-sm text-green-400">
                ${Math.round((plan.price_annual / 12) * 100) / 100}/month billed annually
              </div>
            )}
          </div>

          {/* Trial */}
          {plan.trial_days > 0 && (
            <div className="mb-4 text-sm text-blue-400">
              {plan.trial_days} day free trial
            </div>
          )}

          {/* Features */}
          <div className="mb-6 space-y-2">
            {plan.features.slice(0, 5).map((feature, idx) => (
              <div key={idx} className="flex items-center gap-2 text-sm text-slate-300">
                <CheckCircle className="w-4 h-4 text-green-500" />
                {feature}
              </div>
            ))}
            {plan.features.length > 5 && (
              <div className="text-xs text-slate-400">
                +{plan.features.length - 5} more features
              </div>
            )}
          </div>

          {/* Storage */}
          <div className="mb-6 text-sm">
            <div className="text-slate-400">Storage</div>
            <div className="text-lg font-semibold text-slate-100">
              {plan.storage_gb}GB
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-2">
            <button
              onClick={() => onSelectPlan?.(plan.tier, 'monthly')}
              className={`w-full py-2 px-4 rounded-lg font-medium transition ${
                plan.tier === 'professional'
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-slate-700 hover:bg-slate-600 text-slate-100'
              }`}
            >
              Choose Plan
            </button>
            {plan.price_annual && (
              <button
                onClick={() => onSelectPlan?.(plan.tier, 'annual')}
                className="w-full py-2 px-4 rounded-lg font-medium bg-slate-700 hover:bg-slate-600 text-slate-100 transition text-sm"
              >
                Save 17% Yearly
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export const StripeCheckout: React.FC<CheckoutProps> = ({
  onSuccess,
  onError,
}) => {
  const { user } = useAuthStore();
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const plan = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '').get('plan') || 'starter';
  const cycle = new URLSearchParams(typeof window !== 'undefined' ? window.location.search : '').get('cycle') || 'monthly';

  useEffect(() => {
    const createCheckoutSession = async () => {
      try {
        const response = await apiClient.post('/api/payments/checkout', {
          tier: plan,
          billing_cycle: cycle,
          success_url: `${window.location.origin}/account/billing?status=success`,
          cancel_url: `${window.location.origin}/pricing`,
        });

        setClientSecret(response.session_id);
      } catch (error) {
        console.error('Failed to create checkout session:', error);
        onError?.('Failed to create checkout session');
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      createCheckoutSession();
    }
  }, [user, plan, cycle]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-slate-400">Preparing checkout...</div>
      </div>
    );
  }

  if (!clientSecret) {
    return (
      <div className="flex items-center gap-3 p-4 bg-red-900/20 rounded-lg border border-red-700 text-red-400">
        <AlertCircle className="w-5 h-5" />
        Failed to load checkout. Please try again.
      </div>
    );
  }

  return (
    <EmbeddedCheckoutProvider stripe={stripePromise} options={{ clientSecret }}>
      <EmbeddedCheckout onComplete={onSuccess} />
    </EmbeddedCheckoutProvider>
  );
};
