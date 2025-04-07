## fedcal, a democratic python calendar enhancement to pandas

![fedcal logo](docs/imgs/fedcal-sm.png)

Current version - unstable alpha 0.1

fedcal is a simple calendar library with **_one big goal big goal_:** **enable new perspective on the U.S. Government to build transparency, improve government, and bolster democracy.**

### a calendar... why?

The U.S. Government is massive. Over two million civilian and military employees. 1.7 _trillion_ dollars in FY23 spending. Even tiny and short-lived changes and shifts in the government workforce and spending can have far-reaching impacts _over time_.

Time is at the heart of those impacts. I'm a federal manager, and I started writing fedcal because I wanted to understand how shifts in personnel availability, seasonality, and budgetary factors impacted productivity to help me plan and drive better results. For example, I know first hand how devastating the continuing resolution cycle can be on productivity and outcomes, but didn't know _precisely how devastating_ those impacts could be (or how subtle and unexpected). **I was shocked to find there weren't off-the-shelf solutions for understanding the basic rhythms and routines of the massive U.S. Government machine**

### fedcal is about answering big and small questions, improving predictions, and understanding the U.S. Government, its effect on society and the world

> [!NOTE]
> The Federal Government is a big control group (of sorts) if you think about it. **Two million people are mostly at work... or they aren't** because of holidays, weekends, military passdays, or government shutdowns. One minute the government is 'on', and the next it is 'off'. Of course, it's more complicated than that -- sometimes only half, a third, or 90% of the government is impacted, which offers opportunities for even richer differential analysis (and one fedcal hopes to enable). But it's not just shutdowns -- a continuing resolution instead of a full year appropriation is another kind of binary relationship, or even whether a holiday falls on a Monday or Tuesday. fedcal aims to give you the tools to explore these relationships and their significance (...or insignificance).

#### A few example questions fedcal can help answer:

##### productivity analysis

- What impacts do continuing resolutions (CRs), full-year appropriations, and, of course, shutdowns, have on Federal services? How long do those impacts linger, and how quickly, when, and how are they propagated?
- Which departments feel these impacts the most?
- How do holidays and military passdays affect seasonal outcomes and workforce productivity? How long do those effects extend?
- How do those same factors impact Federal contractor productivity? ... private business? ...agriculture? ...industrial security?

##### economic/financial analysis

- How do changes in federal appropriations (i.e. full-year appropriations, continuing resolutions, gaps/shutdowns) affect not just the U.S. economy, but state, local, international economies? Federal contractors and employees? Businesses reliant on federal employees?
- How fast do those impacts propagate? How quickly do they heal?
- How do federal paydays and holidays impact small businesses and local economies (e.g. for a military town, or a deli across the street from a federal building)?

##### business and human resources analysis

- How do changes in U.S. Government budgeting and productivity impact contracting and demand? Are they accurately predictable? How long does it take those shifts to propagate into financial outcomes for businesses dependent on the Government.
- How do shifts in government budgeting or personnel affect supply and demand for human capital? Federal hiring? Talent availability?

##### social science

- Are Congress' irregularities more routine and predictable than they might appear? Are certain committees more consistently effective at passing appropriations? Why?
- What are the social, political, and economic costs of irregular Federal budgeting?
- What unexpected correlations are there for leave or short interruptions in personnel from holidays, military passes, and similar factors (e.g. Some shots in the dark: are smokeless tobacco sales measurably impacted by military leave in military communities? Are certain crimes more or less likely when federal employees get Christmas Eve off? Do military passdays alter dependent educational outcomes in subsequent weeks)?
- Are federal employees more likely to make certain purchases or financial decisions before or after paydays?

##### more routine stuff

Of course, as a calendar library, fedcal can help you streamline more development for routine needs like:

- leave and pay automation systems
- financial systems (i.e. bank holidays, deposit prediction (hello USAA!))
- informational websites
- whatever else you can think up

### okay, I'm sold, but what does it do?

**The fedcal API bolts on Federal data/time information enhancements to two of the most powerful classes in data science for time series analysis - pandas' `Timestamp` and `DatetimeIndex`:**

1. `FedStamp` - fedcal's enhanced sub-class to [pandas' Timestamp class](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Timestamp.html)

2. `FedIndex` a companion class that adds similar functionality to [pandas' DatetimeIndex class](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DatetimeIndex.html#pandas-datetimeindex)

> [!IMPORTANT]
> `FedStamp` and `FedIndex` **retain all functionality** of pandas `Timestamp` and `DatetimeIndex`. (... or they should, pending testing and refinement and your issue submissions...)

### Core Enhancements to Timestamp and DatetimeIndex

1. **Department-level appropriations/operational status for all top-level Federal Departments over time**, with shutdown and appropriations gap data from FY75 to present, and continuing resolutions data from FY99 to present (currently -- I plan to delve back to FY75 eventually)

2. Federal date attributes 1970 to whenever:

   - **Federal Holidays, including historical holidays by Presidential proclamation** (also back to FY75).
   - **Federal businessdays** (1970 to indefinite future - why 1970? I use POSIX time as a reasonable floor; no other reason.)
   - **Federal fiscal years and fiscal quarters** (1970 to whenever)
   - fedcal can even take a very rough guess of whether a future President will declare a given Christmas Eve a holiday

3. Federal **civilian biweekly paydays**

4. **Military paydays and estimated holiday passdays**

5. Supporting time utilities like `to_timestamp` and `to_datetimeindex`

6. Suggestions?

### what's next?

- Lots of bug fixes before initial alpha
- error handling
- thorough test coverage
- CI/CD pipeline and packaging for pypi deployment
- fullsome documentation
- performance optimizations (e.g. vectorize date range lookups for department statuses)
- API enhancements (e.g. feature encoding) and removing artifacts of design changes
- adding CR data to FY75

### how can I help?

Review the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) and [CONTRIBUTING.md](CONTRIBUTING.md) to get started. Please help!
