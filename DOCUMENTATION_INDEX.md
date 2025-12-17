Documentation Index
Quick reference guide to navigate all documentation for the NiFi Metrics Collector.

📚 Main Documentation
README.md
Start here! Main project documentation covering:

Project overview and key features
Installation instructions
Deployment model (distributed agents)
Configuration guide
Metric collection setup
Storage options (AWS, Azure, Local)
Quick start examples

Read this first if you're:

New to the project
Setting up the collector
Configuring metrics collection
Deploying to NiFi nodes


README_ANALYSIS.md
Complete analysis guide covering the troubleshooting tool:

Interactive CLI usage
All analysis commands (30+ commands)
Provenance analysis guide
Health monitoring
Performance troubleshooting
Workflow examples
Advanced usage

Read this if you're:

Using the analysis tool
Troubleshooting NiFi flows
Analyzing provenance data
Investigating data loss or performance issues


🔧 Technical Documentation
VERSIONING.md
Schema versioning implementation guide:

Version management system
How to add new versions
Compatibility checking
Migration strategies
Best practices

Read this if you're:

Contributing to the project
Upgrading between versions
Understanding data compatibility
Planning schema changes


VERSION_QUICKREF.md
Quick reference for developers:

Common code snippets
Version checking commands
Quick troubleshooting
API reference

Read this if you're:

Developing features
Need quick version info
Writing scripts
Debugging version issues


INTEGRATION_SUMMARY.md
How versioning integrates with the system:

Collection side integration
Analysis side integration
End-to-end flow
Architecture diagrams

Read this if you're:

Understanding system architecture
Contributing major features
Reviewing integration points


📖 User Guides
PROVENANCE_ANALYSIS_GUIDE.md
Detailed provenance analysis guide:

All provenance commands explained
Real-world use cases
Workflow examples
Best practices
Troubleshooting tips

Read this if you're:

Using provenance analysis features
Investigating data loss
Tracing FlowFile lineage
Optimizing flow performance


PROVENANCE_FEATURES_SUMMARY.md
Complete provenance feature overview:

Feature summary
Command reference
Use cases and examples
Technical architecture
Business impact

Read this if you're:

Learning about provenance features
Evaluating capabilities
Presenting to management
Planning implementation


QUICKSTART_VERSIONS.md
5-minute version system guide:

Quick start steps
Common scenarios
Troubleshooting
What you need to know

Read this if you're:

Getting started quickly
Need basic version info
Handling version errors
Learning the basics


🚀 Getting Started Paths
Path 1: First Time Setup
1. README.md (Installation & Configuration)
2. Run collector on one node
3. README_ANALYSIS.md (Analysis basics)
4. Try the troubleshooting tool
Path 2: Learning Analysis
1. README_ANALYSIS.md (Command reference)
2. PROVENANCE_ANALYSIS_GUIDE.md (Detailed guide)
3. Try commands on your data
4. Review workflow examples
Path 3: Understanding Versioning
1. QUICKSTART_VERSIONS.md (5-minute intro)
2. Use the version commands
3. VERSIONING.md (Full details if needed)
Path 4: Contributing
1. README.md (Project overview)
2. VERSIONING.md (Version system)
3. INTEGRATION_SUMMARY.md (Architecture)
4. Review code in lib/ and analysis/lib/

🔍 Quick Find
"How do I...?"
TaskDocumentSectionInstall the collectorREADME.mdInstallationConfigure metricsREADME.mdConfigurationRun the collectorREADME.mdPart 1: Metric CollectionUse the analysis toolREADME_ANALYSIS.mdQuick StartFind dropped FlowFilesREADME_ANALYSIS.mdProvenance AnalysisTrace a FlowFileREADME_ANALYSIS.mdtrace-flowfile commandCheck versionsQUICKSTART_VERSIONS.mdQuick CommandsUnderstand provenancePROVENANCE_ANALYSIS_GUIDE.mdOverviewAdd new featuresVERSIONING.mdAdding New VersionsFix version errorsQUICKSTART_VERSIONS.mdTroubleshootingDeploy to clusterREADME.mdDeployment ModelOptimize performanceREADME_ANALYSIS.mdTypical Workflows

📁 File Organization
nifi_metrics_collector/
├── README.md                           # Main documentation (START HERE)
├── README_ANALYSIS.md                  # Analysis tool guide
├── DOCUMENTATION_INDEX.md              # This file
│
├── docs/versioning/
│   ├── VERSIONING.md                   # Complete version guide
│   ├── VERSION_QUICKREF.md             # Quick reference
│   ├── QUICKSTART_VERSIONS.md          # 5-minute guide
│   └── INTEGRATION_SUMMARY.md          # Integration details
│
├── docs/provenance/
│   ├── PROVENANCE_ANALYSIS_GUIDE.md    # Detailed guide
│   └── PROVENANCE_FEATURES_SUMMARY.md  # Feature overview
│
├── docs/setup/
│   └── CLEANUP.md                      # Cleanup guide
│
└── [other files...]
Note: Documents are currently in the root directory. Consider organizing into subdirectories as shown above.

📊 Documentation by Role
For Operators

README.md - Setup and deployment
README_ANALYSIS.md - Daily troubleshooting
PROVENANCE_ANALYSIS_GUIDE.md - Advanced analysis

For Developers

VERSIONING.md - Version management
INTEGRATION_SUMMARY.md - Architecture
VERSION_QUICKREF.md - Code snippets

For Managers

README.md - Project overview
PROVENANCE_FEATURES_SUMMARY.md - Capabilities & ROI
README_ANALYSIS.md - Analysis capabilities

For New Users

README.md - Start here
QUICKSTART_VERSIONS.md - Quick version intro
README_ANALYSIS.md - Basic commands


🆘 Getting Help
Common Issues
ProblemSeeSectionInstallation failsREADME.mdInstallationCan't load dataREADME_ANALYSIS.mdTroubleshootingVersion errorsQUICKSTART_VERSIONS.mdTroubleshootingNo provenance dataPROVENANCE_ANALYSIS_GUIDE.mdCommon IssuesCollector not runningREADME.mdPart 1Analysis tool errorsREADME_ANALYSIS.mdTroubleshooting
Support Resources

GitHub Issues: Report bugs or request features
Documentation: You're reading it!
Code Comments: Inline documentation in source files
Example Configs: Template files in config/


🔄 Keeping Documentation Updated
When making changes:

Update relevant documentation
Check cross-references
Update this index if adding new docs
Update version history if applicable


Summary

Start: README.md
Analyze: README_ANALYSIS.md
Versions: QUICKSTART_VERSIONS.md
Provenance: PROVENANCE_ANALYSIS_GUIDE.md
Develop: VERSIONING.md

Can't find what you're looking for? Check the "Quick Find" table above or open an issue on GitHub.
