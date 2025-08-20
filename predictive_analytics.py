#!/usr/bin/env python3
"""
Predictive Analytics Engine - Phase 3: Advanced Features
Predicts when VMs will reach critical thresholds and detects cluster-wide issues
"""

import json
import time
import statistics
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging

class PredictiveAnalyticsEngine:
    def __init__(self):
        self.historical_data_file = Path(__file__).parent / "logs" / "vm_historical_data.json"
        self.predictions_file = Path(__file__).parent / "logs" / "vm_predictions.json"
        self.cluster_patterns_file = Path(__file__).parent / "logs" / "cluster_patterns.json"
        
        self.historical_data = self.load_historical_data()
        self.cluster_patterns = self.load_cluster_patterns()
        
        # Keep 7 days of historical data
        self.max_history_days = 7
        self.max_prediction_horizon = 4 * 60  # 4 hours in minutes
        
    def load_historical_data(self) -> Dict:
        """Load historical VM performance data"""
        if self.historical_data_file.exists():
            try:
                with open(self.historical_data_file, "r") as f:
                    data = json.load(f)
                    # Clean old data (older than max_history_days)
                    cutoff = time.time() - (self.max_history_days * 24 * 60 * 60)
                    for vm_name in list(data.keys()):
                        if vm_name in data:
                            data[vm_name] = [
                                entry for entry in data[vm_name] 
                                if entry.get("timestamp", 0) > cutoff
                            ]
                            if not data[vm_name]:
                                del data[vm_name]
                    return data
            except:
                return {}
        return {}
        
    def save_historical_data(self):
        """Save historical VM performance data"""
        try:
            with open(self.historical_data_file, "w") as f:
                json.dump(self.historical_data, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save historical data: {e}")
            
    def load_cluster_patterns(self) -> Dict:
        """Load cluster-wide pattern analysis"""
        if self.cluster_patterns_file.exists():
            try:
                with open(self.cluster_patterns_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}
        
    def save_cluster_patterns(self):
        """Save cluster pattern analysis"""
        try:
            with open(self.cluster_patterns_file, "w") as f:
                json.dump(self.cluster_patterns, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save cluster patterns: {e}")
            
    def record_vm_metrics(self, vm_data: List[Dict]):
        """Record current VM metrics for historical analysis"""
        timestamp = time.time()
        
        for vm in vm_data:
            vm_name = vm.get("name") or vm.get("host", "Unknown")
            
            if vm_name not in self.historical_data:
                self.historical_data[vm_name] = []
                
            # Record current metrics
            metrics = {
                "timestamp": timestamp,
                "cpu_usage": vm.get("cpu_usage", 0),
                "memory_usage": vm.get("memory_usage", 0),
                "disk_usage": vm.get("disk_usage", 0),
                "status": vm.get("status", "Unknown"),
                "health": vm.get("health", 0)
            }
            
            self.historical_data[vm_name].append(metrics)
            
            # Keep only recent data points (24 hours worth, assuming 5-minute intervals)
            max_points = int((24 * 60) / 5)  # 288 data points
            if len(self.historical_data[vm_name]) > max_points:
                self.historical_data[vm_name] = self.historical_data[vm_name][-max_points:]
                
        self.save_historical_data()
        
    def calculate_trend(self, values: List[float], time_window: int = 12) -> Tuple[float, str]:
        """Calculate trend slope and direction"""
        if len(values) < 2:
            return 0.0, "stable"
            
        # Use last time_window points or all available points
        recent_values = values[-time_window:] if len(values) >= time_window else values
        
        if len(recent_values) < 2:
            return 0.0, "stable"
            
        # Simple linear regression for trend
        n = len(recent_values)
        x_values = list(range(n))
        
        # Calculate slope
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(recent_values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, recent_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0.0, "stable"
            
        slope = numerator / denominator
        
        # Determine trend direction
        if slope > 0.5:
            direction = "increasing"
        elif slope < -0.5:
            direction = "decreasing"
        else:
            direction = "stable"
            
        return slope, direction
        
    def predict_critical_threshold(self, vm_name: str, metric_type: str, current_value: float, threshold: float) -> Optional[Dict]:
        """Predict when a VM metric will reach critical threshold"""
        if vm_name not in self.historical_data:
            return None
            
        vm_history = self.historical_data[vm_name]
        if len(vm_history) < 6:  # Need at least 30 minutes of data
            return None
            
        # Extract metric values
        metric_values = [entry.get(f"{metric_type}_usage", 0) for entry in vm_history]
        
        # Calculate trend
        slope, direction = self.calculate_trend(metric_values)
        
        if direction != "increasing" or slope <= 0:
            return None  # Not trending toward critical
            
        # Predict time to reach threshold
        if current_value >= threshold:
            return None  # Already at threshold
            
        remaining_increase = threshold - current_value
        if slope <= 0:
            return None
            
        # Time to reach threshold (in data points, each point is ~5 minutes)
        time_points = remaining_increase / slope
        minutes_to_critical = time_points * 5  # 5-minute intervals
        
        if minutes_to_critical > self.max_prediction_horizon:
            return None  # Too far in the future to be reliable
            
        prediction_time = datetime.now() + timedelta(minutes=minutes_to_critical)
        
        confidence = self.calculate_prediction_confidence(metric_values, slope)
        
        return {
            "vm_name": vm_name,
            "metric": metric_type,
            "current_value": current_value,
            "threshold": threshold,
            "predicted_time": prediction_time.isoformat(),
            "minutes_to_critical": int(minutes_to_critical),
            "trend_slope": slope,
            "confidence": confidence
        }
        
    def calculate_prediction_confidence(self, values: List[float], slope: float) -> float:
        """Calculate confidence level for prediction"""
        if len(values) < 3:
            return 0.1
            
        # Calculate R-squared for trend line fit
        recent_values = values[-12:]  # Last hour of data
        n = len(recent_values)
        
        if n < 3:
            return 0.2
            
        x_values = list(range(n))
        y_mean = statistics.mean(recent_values)
        
        # Predicted values using linear trend
        x_mean = statistics.mean(x_values)
        predicted_values = [slope * (x - x_mean) + y_mean for x in x_values]
        
        # Calculate R-squared
        ss_res = sum((actual - predicted) ** 2 for actual, predicted in zip(recent_values, predicted_values))
        ss_tot = sum((actual - y_mean) ** 2 for actual in recent_values)
        
        if ss_tot == 0:
            return 0.3
            
        r_squared = 1 - (ss_res / ss_tot)
        
        # Convert R-squared to confidence (0.0 to 1.0)
        confidence = max(0.1, min(0.95, r_squared))
        
        return confidence
        
    def detect_cluster_wide_issues(self, vm_data: List[Dict]) -> List[Dict]:
        """Detect cluster-wide patterns that indicate infrastructure issues"""
        cluster_issues = []
        
        if len(vm_data) < 5:  # Need meaningful sample size
            return cluster_issues
            
        # Analyze current metrics across all VMs
        cpu_values = [vm.get("cpu_usage", 0) for vm in vm_data if vm.get("status") == "Online"]
        memory_values = [vm.get("memory_usage", 0) for vm in vm_data if vm.get("status") == "Online"]
        disk_values = [vm.get("disk_usage", 0) for vm in vm_data if vm.get("status") == "Online"]
        
        offline_count = len([vm for vm in vm_data if vm.get("status") != "Online"])
        total_vms = len(vm_data)
        
        # Check for cluster-wide high resource usage
        if cpu_values:
            avg_cpu = statistics.mean(cpu_values)
            high_cpu_count = len([cpu for cpu in cpu_values if cpu > 70])
            
            if avg_cpu > 60 and high_cpu_count / len(cpu_values) > 0.5:
                cluster_issues.append({
                    "type": "cluster_cpu_high",
                    "message": f"🚨 Cluster-wide CPU issue detected",
                    "details": f"Average CPU: {avg_cpu:.1f}%, {high_cpu_count}/{len(cpu_values)} VMs >70%",
                    "severity": "high",
                    "affected_count": high_cpu_count,
                    "suggestion": "Check storage subsystem, network congestion, or resource contention"
                })
                
        # Check for multiple VM failures
        if offline_count > 1 and (offline_count / total_vms) > 0.1:
            cluster_issues.append({
                "type": "cluster_multiple_offline",
                "message": f"🔴 Multiple VM failures detected",
                "details": f"{offline_count} VMs offline ({(offline_count/total_vms*100):.1f}% of infrastructure)",
                "severity": "critical",
                "affected_count": offline_count,
                "suggestion": "Check hypervisor status, network connectivity, storage availability"
            })
            
        # Check for storage issues (multiple VMs with high disk usage)
        if disk_values:
            high_disk_count = len([disk for disk in disk_values if disk > 80])
            
            if high_disk_count > 2 and (high_disk_count / len(disk_values)) > 0.3:
                cluster_issues.append({
                    "type": "cluster_storage_issue",
                    "message": f"🚨 Possible storage subsystem issue",
                    "details": f"{high_disk_count} VMs with disk >80%",
                    "severity": "high",
                    "affected_count": high_disk_count,
                    "suggestion": "Check shared storage, SAN connectivity, disk array health"
                })
                
        return cluster_issues
        
    def generate_predictive_alerts(self, vm_data: List[Dict]) -> List[Dict]:
        """Generate predictive alerts for VMs approaching critical thresholds"""
        predictive_alerts = []
        
        # Record current metrics for historical analysis
        self.record_vm_metrics(vm_data)
        
        # Generate predictions for each VM
        for vm in vm_data:
            vm_name = vm.get("name") or vm.get("host", "Unknown")
            
            if vm.get("status") != "Online":
                continue
                
            # Predict CPU critical
            cpu_prediction = self.predict_critical_threshold(
                vm_name, "cpu", vm.get("cpu_usage", 0), 85
            )
            
            if cpu_prediction and cpu_prediction["confidence"] > 0.6:
                predictive_alerts.append({
                    "type": "predictive_cpu",
                    "vm": vm_name,
                    "message": f"⚠️ PREDICTIVE: {vm_name} CPU will reach critical in {cpu_prediction['minutes_to_critical']} minutes",
                    "prediction": cpu_prediction,
                    "level": "WARNING"
                })
                
            # Predict Memory critical
            memory_prediction = self.predict_critical_threshold(
                vm_name, "memory", vm.get("memory_usage", 0), 90
            )
            
            if memory_prediction and memory_prediction["confidence"] > 0.6:
                predictive_alerts.append({
                    "type": "predictive_memory",
                    "vm": vm_name,
                    "message": f"⚠️ PREDICTIVE: {vm_name} Memory will reach critical in {memory_prediction['minutes_to_critical']} minutes",
                    "prediction": memory_prediction,
                    "level": "WARNING"
                })
                
            # Predict Disk critical
            disk_prediction = self.predict_critical_threshold(
                vm_name, "disk", vm.get("disk_usage", 0), 90
            )
            
            if disk_prediction and disk_prediction["confidence"] > 0.6:
                predictive_alerts.append({
                    "type": "predictive_disk",
                    "vm": vm_name,
                    "message": f"⚠️ PREDICTIVE: {vm_name} Disk will reach critical in {disk_prediction['minutes_to_critical']} minutes",
                    "prediction": disk_prediction,
                    "level": "WARNING"
                })
                
        # Detect cluster-wide issues
        cluster_issues = self.detect_cluster_wide_issues(vm_data)
        for issue in cluster_issues:
            predictive_alerts.append({
                "type": issue["type"],
                "vm": "CLUSTER",
                "message": issue["message"],
                "details": issue["details"],
                "suggestion": issue["suggestion"],
                "level": "CRITICAL" if issue["severity"] == "critical" else "WARNING"
            })
            
        return predictive_alerts
        
    def format_predictive_alert(self, alert: Dict) -> str:
        """Format predictive alert with rich information"""
        now = datetime.now()
        
        if alert["vm"] == "CLUSTER":
            # Cluster-wide issue
            return f"""🚨 Infrastructure Alert
🏗️ Scope: Cluster-wide Issue
⏰ Time: {now.strftime('%H:%M:%S')}

{alert['message']}

📊 Details:
• {alert['details']}
• Severity: {alert.get('severity', 'high').upper()}
• Affected: {alert.get('suggestion', 'Multiple systems')}

💡 Recommended Actions:
• {alert.get('suggestion', 'Contact infrastructure team')}
• Escalate to system administrators
• Monitor cluster health dashboard

---
Predictive Analytics Engine v3.0
One Climate Infrastructure"""
        else:
            # Individual VM prediction
            prediction = alert.get("prediction", {})
            confidence = prediction.get("confidence", 0) * 100
            
            return f"""⚠️ Predictive Alert
🖥️ VM: {alert['vm']}
📈 Type: Resource Trend Analysis
⏰ Time: {now.strftime('%H:%M:%S')}

🔮 Prediction:
• Metric: {prediction.get('metric', 'N/A').upper()}
• Current: {prediction.get('current_value', 0):.1f}%
• Will reach: {prediction.get('threshold', 0):.1f}% (Critical)
• ETA: {prediction.get('minutes_to_critical', 0)} minutes
• Confidence: {confidence:.1f}%

📊 Trend Analysis:
• Direction: Increasing
• Rate: {prediction.get('trend_slope', 0):.2f}%/interval
• Based on: Last 1 hour of data

💡 Proactive Actions:
• Scale resources before critical threshold
• Check for resource-intensive processes
• Consider load balancing or migration
• Monitor closely for next 30 minutes

---
Predictive Analytics Engine v3.0
Advanced Monitoring System"""

def main():
    """Test function for predictive analytics"""
    engine = PredictiveAnalyticsEngine()
    
    # Test with sample VM data
    sample_vm_data = [
        {
            "name": "Test-VM-01",
            "cpu_usage": 75.0,
            "memory_usage": 82.0,
            "disk_usage": 65.0,
            "status": "Online",
            "health": 85
        },
        {
            "name": "Test-VM-02", 
            "cpu_usage": 45.0,
            "memory_usage": 60.0,
            "disk_usage": 85.0,
            "status": "Online",
            "health": 90
        }
    ]
    
    # Generate predictive alerts
    alerts = engine.generate_predictive_alerts(sample_vm_data)
    
    print(f"Generated {len(alerts)} predictive alerts:")
    for alert in alerts:
        print("=" * 60)
        print(engine.format_predictive_alert(alert))
        print("=" * 60)

if __name__ == "__main__":
    main()