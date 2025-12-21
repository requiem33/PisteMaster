export default {
    listTitle: '赛事列表',
    createTitle: '开启新赛事',
    dashboard: {
        title: '赛事控制台',
        tournamentStatus: '进行中',
        editInfo: '编辑赛事信息',
        addEvent: '新增竞赛项目',
        stats: {
            totalEvents: '项目总数',
            totalFencers: '已报名选手',
            activePistes: '当前活跃剑道',
            syncStatus: '同步状态',
            realtime: '实时'
        },
        eventSection: '竞赛项目',
        filterAll: '全部',
        filterIndividual: '个人赛',
        filterTeam: '团体赛',
        noEvents: '暂无项目，点击右上角创建第一个单项',
        breadcrumb: {
            home: '首页',
            tournamentList: '赛事列表',
            currentTournament: '当前赛事'
        }
    },
    eventDrawer: {
        title: '创建竞赛项目',
        form: {
            eventName: '项目名称',
            eventType: '剑种类型',
            rule: '应用规则',
            eventNature: '比赛性质',
            startTime: '预定开始时间',
            individual: '个人赛',
            team: '团体赛'
        },
        placeholder: {
            eventName: '例如：U14 男子重剑个人赛',
            eventType: '请选择剑种',
            rule: '请选择赛制规则',
            startTime: '选择时间'
        },
        alert: {
            title: '提示',
            description: '创建项目后，您将进入选手录入与小组编排环节。'
        },
        messages: {
            eventNameRequired: '请输入项目名称',
            eventTypeRequired: '请选择剑种',
            ruleRequired: '请选择规则',
            createSuccess: '竞赛项目创建成功'
        },
        actions: {
            cancel: '取消',
            confirmCreate: '确认创建'
        }
    },
    form: {
        name: '赛事名称',
        organizer: '主办单位',
        location: '比赛地点',
        date: '比赛日期',
        rangeSeparator: '至',
        startPlaceholder: '开始日期',
        endPlaceholder: '结束日期',
        rule: '比赛规则',
        placeholder: {
            name: '请输入赛事名称',
            organizer: '请输入主办单位名称',
            location: '请输入比赛地点'
        }
    },
    messages: {
        nameRequired: '赛事名称不能为空',
        dateRequired: '请选择比赛日期',
        createSuccess: '赛事创建成功',
        createFailed: '创建失败，请重试'
    },
    actions: {
        cancel: '取消',
        createAndEnter: '创建并进入编排'
    }
}