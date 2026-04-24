#!/usr/bin/env python3
"""
Benchmark script for testing API performance
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict
import argparse

# Sample test data
SAMPLE_INFER_DATA = {
    "data": [
        {
            "id": f"test_{i}",
            "index": "61b8715499ce4372a5d739a0",
            "category": "Finance",
            "type": "post",
            "title": f"Test title {i}",
            "content": f"This is test content number {i} for spam detection testing",
            "description": f"Test description {i}",
            "site_id": "123456789",
            "parent_id": "",
            "topic": "test"
        }
        for i in range(40)  # 40 items per request
    ]
}

SAMPLE_SPAM_DATA = {
    "items": [
        {
            "id": f"spam_test_{i}",
            "index": "test_index",
            "title": f"Spam test title {i}",
            "content": f"This is spam test content {i}",
            "description": f"Spam test description {i}"
        }
        for i in range(40)  # 40 items per request
    ]
}

class APIBenchmark:
    def __init__(self, base_url: str = "http://localhost:8990"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=50,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
        )
        timeout = aiohttp.ClientTimeout(total=120)  # 2 minute timeout
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def health_check(self) -> bool:
        """Check if API is healthy"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False

    async def single_request(self, endpoint: str, data: dict) -> Dict:
        """Make a single API request"""
        start_time = time.time()
        try:
            async with self.session.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                response_data = await response.json()
                end_time = time.time()
                
                return {
                    "success": response.status == 200,
                    "status_code": response.status,
                    "response_time": end_time - start_time,
                    "response_size": len(json.dumps(response_data)),
                    "error": None if response.status == 200 else response_data
                }
        except Exception as e:
            end_time = time.time()
            return {
                "success": False,
                "status_code": 0,
                "response_time": end_time - start_time,
                "response_size": 0,
                "error": str(e)
            }

    async def concurrent_requests(self, endpoint: str, data: dict, 
                                num_requests: int, concurrency: int) -> List[Dict]:
        """Make concurrent requests"""
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_request():
            async with semaphore:
                return await self.single_request(endpoint, data)
        
        tasks = [bounded_request() for _ in range(num_requests)]
        results = await asyncio.gather(*tasks)
        return results

    def analyze_results(self, results: List[Dict]) -> Dict:
        """Analyze benchmark results"""
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        if not successful_results:
            return {
                "total_requests": len(results),
                "successful_requests": 0,
                "failed_requests": len(failed_results),
                "success_rate": 0.0,
                "error": "All requests failed"
            }
        
        response_times = [r["response_time"] for r in successful_results]
        response_sizes = [r["response_size"] for r in successful_results]
        
        return {
            "total_requests": len(results),
            "successful_requests": len(successful_results),
            "failed_requests": len(failed_results),
            "success_rate": len(successful_results) / len(results) * 100,
            "response_time": {
                "min": min(response_times),
                "max": max(response_times),
                "mean": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times),
                "p99": statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else max(response_times)
            },
            "throughput": {
                "requests_per_second": len(successful_results) / max(response_times) if response_times else 0,
                "avg_response_size": statistics.mean(response_sizes) if response_sizes else 0
            },
            "errors": [r["error"] for r in failed_results if r["error"]]
        }

    async def run_benchmark(self, endpoint: str, data: dict, 
                          num_requests: int, concurrency: int) -> Dict:
        """Run complete benchmark"""
        print(f"🚀 Starting benchmark:")
        print(f"   Endpoint: {endpoint}")
        print(f"   Requests: {num_requests}")
        print(f"   Concurrency: {concurrency}")
        print(f"   Items per request: {len(data.get('data', data.get('items', [])))}")
        
        # Health check first
        if not await self.health_check():
            return {"error": "API health check failed"}
        
        print("✅ API health check passed")
        
        # Run benchmark
        start_time = time.time()
        results = await self.concurrent_requests(endpoint, data, num_requests, concurrency)
        total_time = time.time() - start_time
        
        # Analyze results
        analysis = self.analyze_results(results)
        analysis["total_time"] = total_time
        analysis["overall_rps"] = analysis["successful_requests"] / total_time if total_time > 0 else 0
        
        return analysis

    def print_results(self, results: Dict):
        """Print benchmark results"""
        print("\n" + "="*60)
        print("📊 BENCHMARK RESULTS")
        print("="*60)
        
        if "error" in results:
            print(f"❌ Error: {results['error']}")
            return
        
        # Calculate items processed
        items_per_request = 40  # Default batch size
        total_items = results['successful_requests'] * items_per_request
        items_per_second = total_items / results['total_time'] if results['total_time'] > 0 else 0
        
        print(f"Total Requests: {results['total_requests']}")
        print(f"Successful: {results['successful_requests']}")
        print(f"Failed: {results['failed_requests']}")
        print(f"Success Rate: {results['success_rate']:.2f}%")
        print(f"Total Time: {results['total_time']:.2f}s")
        print(f"Overall RPS: {results['overall_rps']:.2f}")
        print(f"Total Items Processed: {total_items}")
        print(f"Items/Second: {items_per_second:.2f}")
        
        if "response_time" in results:
            rt = results["response_time"]
            print(f"\nResponse Times:")
            print(f"  Min: {rt['min']*1000:.2f}ms")
            print(f"  Max: {rt['max']*1000:.2f}ms")
            print(f"  Mean: {rt['mean']*1000:.2f}ms")
            print(f"  Median: {rt['median']*1000:.2f}ms")
            print(f"  P95: {rt['p95']*1000:.2f}ms")
            print(f"  P99: {rt['p99']*1000:.2f}ms")
        
        if "throughput" in results:
            tp = results["throughput"]
            print(f"\nThroughput:")
            print(f"  Requests/sec: {tp['requests_per_second']:.2f}")
            print(f"  Avg Response Size: {tp['avg_response_size']:.0f} bytes")
        
        if results.get("errors"):
            print(f"\nErrors ({len(results['errors'])}):")
            for error in results["errors"][:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(results["errors"]) > 5:
                print(f"  ... and {len(results['errors']) - 5} more")

async def main():
    parser = argparse.ArgumentParser(description="API Benchmark Tool")
    parser.add_argument("--url", default="http://localhost:8990", help="API base URL")
    parser.add_argument("--endpoint", choices=["infer", "spam", "both"], default="both", 
                       help="Endpoint to test")
    parser.add_argument("--requests", type=int, default=100, help="Number of requests")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent requests")
    parser.add_argument("--items", type=int, default=40, help="Items per request")
    
    args = parser.parse_args()
    
    # Adjust sample data size
    if args.items != 40:
        SAMPLE_INFER_DATA["data"] = SAMPLE_INFER_DATA["data"][:args.items]
        SAMPLE_SPAM_DATA["items"] = SAMPLE_SPAM_DATA["items"][:args.items]
    
    async with APIBenchmark(args.url) as benchmark:
        if args.endpoint in ["infer", "both"]:
            print("🎯 Testing /v1/api/infer endpoint...")
            infer_results = await benchmark.run_benchmark(
                "/v1/api/infer", SAMPLE_INFER_DATA, args.requests, args.concurrency
            )
            benchmark.print_results(infer_results)
        
        if args.endpoint in ["spam", "both"]:
            print("\n🎯 Testing /api/spam endpoint...")
            spam_results = await benchmark.run_benchmark(
                "/api/spam", SAMPLE_SPAM_DATA, args.requests, args.concurrency
            )
            benchmark.print_results(spam_results)

if __name__ == "__main__":
    asyncio.run(main())