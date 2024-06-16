import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const TARGET_VUS = 100;

export let errorRate = new Rate('errors');
export let options = {
  stages: [
      { duration: '1m', target: TARGET_VUS }, 
      { duration: '3m', target: TARGET_VUS },
      { duration: '1m', target: 0 },
  ],
};


export default function () {
  let res = http.post('http://100.20.173.218/log', JSON.stringify({
      message: 'Test log entry',
      level: 'INFO'
  }), {
      headers: { 'Content-Type': 'application/json' },
  });
  let result = check(res, {
    'is status 200': (r) => r.status === 200,
    'transaction time OK': (r) => r.timings.duration < 500,
  });
  errorRate.add(!result);
}