'use client';

import React, { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/auth';
import apiClient from '@/lib/api';
import {
  CreditCard,
  Trash2,
  Plus,
  AlertCircle,
  Check,
  Loader,
} from 'lucide-react';

interface PaymentMethod {
  id: string;
  type: string;
  card_brand?: string;
  card_last4?: string;
  card_exp_month?: number;
  card_exp_year?: number;
  is_default: boolean;
  created_at: string;
}

interface PaymentMethodsProps {
  onAddNew?: () => void;
  editable?: boolean;
}

export const PaymentMethods: React.FC<PaymentMethodsProps> = ({
  onAddNew,
  editable = true,
}) => {
  const { user } = useAuthStore();
  const [methods, setMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    fetchPaymentMethods();
  }, [user]);

  const fetchPaymentMethods = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get('/api/payments/payment-methods');
      setMethods(data.payment_methods || []);
    } catch (err) {
      console.error('Failed to fetch payment methods:', err);
      setError('Failed to load payment methods');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (methodId: string) => {
    if (
      !confirm(
        'Are you sure you want to delete this payment method? You cannot undo this action.'
      )
    ) {
      return;
    }

    try {
      setDeleting(methodId);
      await apiClient.delete(`/api/payments/payment-methods/${methodId}`);
      setMethods((prev) => prev.filter((m) => m.id !== methodId));
    } catch (err) {
      console.error('Failed to delete payment method:', err);
      setError('Failed to delete payment method');
    } finally {
      setDeleting(null);
    }
  };

  const handleSetDefault = async (methodId: string) => {
    try {
      await apiClient.post(`/api/payments/payment-methods/${methodId}/set-default`);
      setMethods((prev) =>
        prev.map((m) => ({
          ...m,
          is_default: m.id === methodId,
        }))
      );
    } catch (err) {
      console.error('Failed to set default payment method:', err);
      setError('Failed to update default payment method');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader className="w-5 h-5 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-900/20 rounded-lg border border-red-700 text-red-400">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {methods.length === 0 ? (
        <div className="text-center py-8">
          <CreditCard className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-400 mb-4">No payment methods added yet</p>
          {editable && onAddNew && (
            <button
              onClick={onAddNew}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white transition"
            >
              <Plus className="w-4 h-4" />
              Add Payment Method
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {methods.map((method) => (
            <div
              key={method.id}
              className="p-4 bg-slate-700/50 rounded-lg border border-slate-600 hover:border-slate-500 transition"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4 flex-1">
                  <div className="w-12 h-8 bg-gradient-to-br from-slate-600 to-slate-700 rounded-lg flex items-center justify-center">
                    <CreditCard className="w-5 h-5 text-slate-300" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-slate-100">
                      <span className="capitalize">{method.card_brand}</span>
                      {' •••• '}
                      <span className="tracking-wider">{method.card_last4}</span>
                    </div>
                    <div className="text-sm text-slate-400">
                      Expires {String(method.card_exp_month).padStart(2, '0')}/
                      {String(method.card_exp_year).slice(-2)}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {method.is_default ? (
                    <span className="inline-flex items-center gap-1 px-3 py-1 bg-green-900/30 border border-green-700 rounded-full text-xs font-medium text-green-400">
                      <Check className="w-3 h-3" />
                      Default
                    </span>
                  ) : (
                    editable && (
                      <button
                        onClick={() => handleSetDefault(method.id)}
                        className="px-3 py-1 text-xs font-medium text-slate-400 hover:text-blue-400 transition"
                      >
                        Set Default
                      </button>
                    )
                  )}

                  {editable && !method.is_default && (
                    <button
                      onClick={() => handleDelete(method.id)}
                      disabled={deleting === method.id}
                      className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition disabled:opacity-50"
                      title="Delete payment method"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}

          {editable && onAddNew && (
            <button
              onClick={onAddNew}
              className="w-full py-3 px-4 border-2 border-dashed border-slate-600 hover:border-slate-500 rounded-lg text-slate-400 hover:text-slate-300 transition flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Payment Method
            </button>
          )}
        </div>
      )}
    </div>
  );
};
