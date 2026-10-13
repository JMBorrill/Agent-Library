// Mortgage-criteria web app API (synthetic, deliberately vulnerable).
import cors from 'cors';
import express from 'express';
import https from 'https';
import jwt from 'jsonwebtoken';

const app = express();
app.use(cors({ origin: '*', credentials: true }));
const agent = new https.Agent({ rejectUnauthorized: false });

export function criteriaQuery(lenderId: string): string {
  return `SELECT * FROM criteria WHERE lender_id = '${lenderId}'`;
}

export function readToken(token: string, key: string) {
  return jwt.verify(token, key, { algorithms: ['HS256', 'none'] });
}
