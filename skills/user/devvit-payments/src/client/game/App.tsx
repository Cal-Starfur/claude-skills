import { usePurchase } from '../hooks/usePurchase';

export const App = () => {
  const { purchaseCount, loading, purchasing, purchaseItem } = usePurchase();

  return (
    <div className="flex flex-col justify-center items-center min-h-screen gap-6 p-4">
      <div className="flex flex-col items-center gap-2">
        <span className="text-6xl">⭐</span>
        <h1 className="text-2xl font-bold text-center text-gray-900">Payments Example</h1>
        <p className="text-sm text-center text-gray-500 max-w-xs">
          This app demonstrates how to integrate payments in Devvit Web.
        </p>
      </div>

      <div className="flex flex-col items-center gap-4">
        <button
          className="flex items-center gap-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white px-6 py-3 rounded-xl font-semibold shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={purchaseItem}
          disabled={loading || purchasing}
        >
          {purchasing ? 'Purchasing...' : 'Purchase Premium Badge'}
        </button>

        {purchaseCount > 0 && (
          <div className="flex items-center gap-2 bg-emerald-100 text-emerald-700 px-4 py-2 rounded-lg">
            <span className="text-lg">✓</span>
            <span className="font-medium">
              Purchased {purchaseCount} {purchaseCount === 1 ? 'time' : 'times'}
            </span>
          </div>
        )}

        {loading && (
          <p className="text-sm text-gray-400">Loading purchase status...</p>
        )}
      </div>
    </div>
  );
};
