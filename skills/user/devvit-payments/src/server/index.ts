import express from 'express';
import { PurchaseStatusResponse } from '../shared/types/api';
import { redis, createServer, context, getServerPort } from '@devvit/web/server';
import type { PaymentHandlerResponse } from '@devvit/web/server';
import { createPost } from './core/post';

const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.text());

const router = express.Router();

// ============================================
// PAYMENTS ENDPOINTS
// ============================================

// Fulfill order - called by Devvit when a purchase is completed
router.post('/internal/payments/fulfill', async (req, res): Promise<void> => {
  try {
    const userId = context.userId;
    const products = req.body.products as Array<{ sku: string }>;

    if (!userId) {
      res.status(400).json({ success: false, error: 'User not authenticated' });
      return;
    }

    if (!products || products.length === 0) {
      res.status(400).json({ success: false, error: 'No products in order' });
      return;
    }

    // Fulfill each product in the order by incrementing the purchase count
    for (const product of products) {
      const key = `purchase:${userId}:${product.sku}`;
      await redis.incrBy(key, 1);
    }

    res.json({ success: true } satisfies PaymentHandlerResponse);
  } catch (error) {
    console.error('Fulfill order error:', error);
    res.status(500).json({ success: false, error: 'Failed to fulfill order' });
  }
});

// Refund order - called by Devvit when a refund is processed
router.post('/internal/payments/refund', async (req, res): Promise<void> => {
  try {
    const userId = context.userId;
    const products = req.body.products as Array<{ sku: string }>;

    if (!userId) {
      res.status(400).json({ success: false, error: 'User not authenticated' });
      return;
    }

    if (!products || products.length === 0) {
      res.status(400).json({ success: false, error: 'No products in order' });
      return;
    }

    // Revoke each product by decrementing the purchase count
    for (const product of products) {
      const key = `purchase:${userId}:${product.sku}`;
      const currentCount = await redis.get(key);
      const count = currentCount ? parseInt(currentCount) : 0;

      if (count > 0) {
        await redis.incrBy(key, -1);
      }
    }

    res.json({ success: true } satisfies PaymentHandlerResponse);
  } catch (error) {
    console.error('Refund order error:', error);
    res.status(500).json({ success: false, error: 'Failed to refund order' });
  }
});

// Get purchase status for the current user
router.get<object, PurchaseStatusResponse | { status: string; message: string }>(
  '/api/purchase-status',
  async (_req, res): Promise<void> => {
    try {
      const userId = context.userId;
      if (!userId) {
        res.status(400).json({ status: 'error', message: 'User not authenticated' });
        return;
      }

      const key = `purchase:${userId}:premium-badge`;
      const count = await redis.get(key);

      res.json({
        type: 'purchase-status',
        purchaseCount: count ? parseInt(count) : 0,
      });
    } catch (error) {
      console.error('Purchase status error:', error);
      res.status(500).json({ status: 'error', message: 'Failed to get purchase status' });
    }
  }
);

// ============================================
// APP LIFECYCLE ENDPOINTS
// ============================================

router.post('/internal/on-app-install', async (_req, res): Promise<void> => {
  try {
    const post = await createPost();
    res.json({
      status: 'success',
      message: `Post created in subreddit ${context.subredditName} with id ${post.id}`,
    });
  } catch (error) {
    console.error(`Error creating post: ${error}`);
    res.status(400).json({ status: 'error', message: 'Failed to create post' });
  }
});

router.post('/internal/menu/post-create', async (_req, res): Promise<void> => {
  try {
    const post = await createPost();
    res.json({
      navigateTo: `https://reddit.com/r/${context.subredditName}/comments/${post.id}`,
    });
  } catch (error) {
    console.error(`Error creating post: ${error}`);
    res.status(400).json({ status: 'error', message: 'Failed to create post' });
  }
});

app.use(router);

const port = getServerPort();
const server = createServer(app);
server.on('error', (err) => console.error(`server error; ${err.stack}`));
server.listen(port);
