#!/usr/bin/env python
"""
Master Test Runner for Tryout Functionality
Runs both basic and advanced test suites and provides comprehensive report
"""

import os
import sys
import time
from datetime import datetime

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

def run_test_suite(test_module_name, test_description):
    """Run a specific test suite and return results"""
    print(f"\n{'='*60}")
    print(f"🧪 {test_description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Import and run the test module
        if test_module_name == 'basic':
            from test_tryout_functionality import main as basic_main
            success = basic_main()
        elif test_module_name == 'advanced':
            from test_advanced_tryout import main as advanced_main
            success = advanced_main()
        else:
            print(f"Unknown test module: {test_module_name}")
            return False, 0
        
        end_time = time.time()
        duration = end_time - start_time
        
        return success, duration
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {str(e)}")
        end_time = time.time()
        duration = end_time - start_time
        return False, duration

def generate_html_report(results):
    """Generate HTML report of test results"""
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Tryout Testing Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .success {{ color: #28a745; }}
        .failure {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .info {{ color: #17a2b8; }}
        .test-suite {{ margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
        .test-suite.passed {{ border-left: 5px solid #28a745; }}
        .test-suite.failed {{ border-left: 5px solid #dc3545; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin-top: 30px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ text-align: center; padding: 15px; background: #fff; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2em; font-weight: bold; }}
        .recommendations {{ background: #e9ecef; padding: 20px; border-radius: 5px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Tryout System Testing Report</h1>
            <p class="info">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value {'success' if results['overall_success'] else 'failure'}">
                    {'✅' if results['overall_success'] else '❌'}
                </div>
                <div>Overall Status</div>
            </div>
            <div class="metric">
                <div class="metric-value">{results['total_suites']}</div>
                <div>Test Suites</div>
            </div>
            <div class="metric">
                <div class="metric-value">{results['passed_suites']}</div>
                <div>Passed Suites</div>
            </div>
            <div class="metric">
                <div class="metric-value">{results['total_duration']:.1f}s</div>
                <div>Total Duration</div>
            </div>
        </div>
"""
    
    # Add individual test suite results
    for suite_name, suite_result in results['suites'].items():
        status_class = 'passed' if suite_result['success'] else 'failed'
        status_icon = '✅' if suite_result['success'] else '❌'
        
        html_content += f"""
        <div class="test-suite {status_class}">
            <h2>{status_icon} {suite_name}</h2>
            <p><strong>Status:</strong> <span class="{'success' if suite_result['success'] else 'failure'}">
                {'PASSED' if suite_result['success'] else 'FAILED'}
            </span></p>
            <p><strong>Duration:</strong> {suite_result['duration']:.2f} seconds</p>
            <p><strong>Description:</strong> {suite_result['description']}</p>
        </div>
"""
    
    # Add summary and recommendations
    html_content += f"""
        <div class="summary">
            <h2>📊 Summary</h2>
            <p>This comprehensive testing suite validates all aspects of the tryout functionality including:</p>
            <ul>
                <li><strong>Basic Functionality:</strong> User authentication, test creation, question navigation, answer submission, scoring, and results display</li>
                <li><strong>Advanced Scenarios:</strong> Time expiration, session management, performance under load, error handling, and data consistency</li>
            </ul>
            
            <div class="recommendations">
                <h3>🔍 Recommendations</h3>
"""
    
    if results['overall_success']:
        html_content += """
                <p class="success"><strong>✅ All tests passed!</strong> The tryout system is functioning correctly and ready for production use.</p>
                <ul>
                    <li>All core functionality is working as expected</li>
                    <li>Performance metrics are within acceptable ranges</li>
                    <li>Error handling is robust and user-friendly</li>
                    <li>Data consistency is maintained across all operations</li>
                </ul>
"""
    else:
        html_content += """
                <p class="failure"><strong>⚠️ Some tests failed.</strong> Please review the failed test suites and address any issues before deploying to production.</p>
                <ul>
                    <li>Check server logs for detailed error information</li>
                    <li>Verify database connectivity and permissions</li>
                    <li>Ensure all required dependencies are installed</li>
                    <li>Test in a staging environment before production deployment</li>
                </ul>
"""
    
    html_content += """
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    # Save HTML report
    report_path = 'tryout_test_report.html'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return report_path

def main():
    """Main function to run all test suites"""
    print("🚀 Starting Comprehensive Tryout Testing")
    print("=" * 60)
    print("This test suite will validate all tryout functionality including:")
    print("• User authentication and permissions")
    print("• Test session management")
    print("• Question navigation and display")
    print("• Answer submission and saving")
    print("• Time management and expiration")
    print("• Score calculation and results")
    print("• Performance and stress testing")
    print("• Error handling and recovery")
    print("=" * 60)
    
    # Test suites to run
    test_suites = [
        ('basic', 'Basic Tryout Functionality Tests'),
        ('advanced', 'Advanced Scenarios and Stress Tests')
    ]
    
    results = {
        'overall_success': True,
        'total_suites': len(test_suites),
        'passed_suites': 0,
        'total_duration': 0,
        'suites': {}
    }
    
    # Run each test suite
    for suite_name, suite_description in test_suites:
        success, duration = run_test_suite(suite_name, suite_description)
        
        results['suites'][suite_description] = {
            'success': success,
            'duration': duration,
            'description': suite_description
        }
        
        results['total_duration'] += duration
        
        if success:
            results['passed_suites'] += 1
        else:
            results['overall_success'] = False
        
        # Small delay between test suites
        time.sleep(2)
    
    # Generate final report
    print(f"\n{'='*80}")
    print("🏁 FINAL TEST REPORT")
    print(f"{'='*80}")
    
    print(f"📊 Test Suites Run: {results['total_suites']}")
    print(f"✅ Passed: {results['passed_suites']}")
    print(f"❌ Failed: {results['total_suites'] - results['passed_suites']}")
    print(f"⏱️  Total Duration: {results['total_duration']:.2f} seconds")
    print(f"📈 Success Rate: {(results['passed_suites']/results['total_suites']*100):.1f}%")
    
    if results['overall_success']:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("✅ The tryout system is fully functional and ready for use!")
        print("✅ All core features are working correctly")
        print("✅ Performance is within acceptable limits")
        print("✅ Error handling is robust")
    else:
        print(f"\n⚠️  SOME TESTS FAILED!")
        print("❌ Please review the failed tests above")
        print("🔧 Fix any issues before deploying to production")
        print("📋 Check the detailed logs for specific error information")
    
    # Generate HTML report
    try:
        report_path = generate_html_report(results)
        print(f"\n📄 Detailed HTML report generated: {report_path}")
        print(f"🌐 Open the report in a web browser for a comprehensive view")
    except Exception as e:
        print(f"\n⚠️  Failed to generate HTML report: {str(e)}")
    
    print(f"\n{'='*80}")
    
    return results['overall_success']

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
