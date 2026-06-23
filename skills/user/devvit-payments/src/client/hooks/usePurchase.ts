import { useCallback, useEffect, useState } from 'react';
import { purchase, OrderResultStatus } from '@devvit/web/client';
import type { PurchaseStatusResponse } from '../../shared/types/api';

type PurchaseState = {
  purchaseCount: number;
  loading: boolean;
  purchasing: boolean;
};

export const usePurchase = () => {
  const [state, setState] = useState<PurchaseState>({
    purchaseCount: 0,
    loading: true,
    purchasing: false,
  });

  // Fetch the user's purchase status on mount
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('/api/purchase-status');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: PurchaseStatusResponse = await res.json();
        setState((prev) => ({ ...prev, purchaseCount: data.purchaseCount, loading: false }));
      } catch (err) {
        console.error('Failed to fetch purchase status', err);
        setState((prev) => ({ ...prev, loading: false }));
      }
    };
    void fetchStatus();
  }, []);

  // Trigger the purchase flow for the premium-badge product
  const purchaseItem = useCallback(async () => {
    setState((prev) => ({ ...prev, purchasing: true }));
    try {
      const result = await purchase('premium-badge');
      if (result.status === OrderResultStatus.STATUS_SUCCESS) {
        setState((prev) => ({
          ...prev,
          purchaseCount: prev.purchaseCount + 1,
          purchasing: false,
        }));
      } else {
        console.error('Purchase failed:', result.errorMessage);
        setState((prev) => ({ ...prev, purchasing: false }));
      }
    } catch (err) {
      console.error('Purchase error:', err);
      setState((prev) => ({ ...prev, purchasing: false }));
    }
  }, []);

  return {
    ...state,
    purchaseItem,
  } as const;
};
