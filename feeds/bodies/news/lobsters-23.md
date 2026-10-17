STAC recently performed STAC-M3™ benchmark audits on a stack featuring the L tick database 1.0 from L Labs PBC running on a single Oxide OxVM cloud virtual machine with 128 vCPUs and 1.25 TiB of RAM, with 5 x 3.44 TB Oxide Local NVMe disks.

STAC-M3 is the industry standard enterprise tick-analytics benchmark for database and hardware stacks that manage large time series of market data. It provides a vendor-neutral framework for evaluating the performance, efficiency, and scalability of time-series databases used in financial analytics and backtesting.

This report covers the baseline suite (Antuco), for performance under fixed conditions. Results for the Shasta suite are available [here](https://docs.stacresearch.com/M3-20261005s).

In these latest tests, the combination of the L tick database and the Oxide OxVM cloud virtual machine achieved the following:

- This solution achieved the highest storage efficiency (STAC-M3.v1.1.STORAGE.EFF) of any published STAC-M3 Antuco result, 364%
  - 1.86x the efficiency of the previous best result (SHK211203)
- This solution outperformed all publicly disclosed results for STAC-M3.β1.1T.YRHIBID-2.TIME
  - 1.81x faster than the previous best result (KDB211210)
- Compared to SUTs using the q language, this solution achieved the fastest mean-response STAC-M3.β1.1T.NBBO.TIME
  - 1.58x faster than the previous best result (KDB230707)
- Was faster in 11 of 17 mean-response time benchmarks than all other publicly disclosed results using a cloud-based deployment architecture
- Outperformed a similar SUT using the q language, NAND flash storage / NVMe SSD, and the same file system (KDB250929) in 9 of 17 mean-response time benchmarks, including:
  - 8.4x speed for STAC-M3.β1.10T.THEOPL.TIME
  - Over 1.7x speedup in STAC-M3.β1.1T.STATS-UI.TIME

The Stack Under Test included:

- Database
  - L tick database 1.0 from L Labs PBC
- Database node
  - 1 x Oxide OxVM cloud virtual machine, with:
  - 1 x 128 vCPU Oxide Virtual Turin-like Processor
  - 1,280 GiB VM memory (1,259 GiB visible to the OS)
  - 5 x 3.44 TB (3,200 GiB) Oxide virtual NVMe disks
- Operating system
  - Ubuntu 24.04.4 LTS

The report provides detailed performance metrics, methodology, and visualizations for the Antuco suite.

The full benchmark report is available for download below. Insights Subscribers can also access detailed system configurations and the code used in this project to reproduce the results in their own environments. To learn more about subscription options, please [contact us](https://docs.stacresearch.com/cdn-cgi/l/email-protection#f0999e969fb0a3a4b1b38295839591829398de939f9d).