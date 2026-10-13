// Mortgage-criteria web app API (synthetic, fixed version).
import cors from 'cors';
import express from 'express';
import jwt from 'jsonwebtoken';

const app = express();
app.use(cors({ origin: ['https://criteria.example-broker.invalid'], credentials: true }));

export const CRITERIA_QUERY = 'SELECT * FROM criteria WHERE lender_id = $1';

export function readToken(token: string, key: string) {
  return jwt.verify(token, key, { algorithms: ['RS256'] });
}
