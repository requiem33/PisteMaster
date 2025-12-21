export default {
    listTitle: 'Tournament List',
    createTitle: 'Start New Tournament',
    dashboard: {
        title: 'Tournament Console',
        tournamentStatus: 'Ongoing',
        editInfo: 'Edit Tournament Info',
        addEvent: 'Add Event',
        stats: {
            totalEvents: 'Total Events',
            totalFencers: 'Registered Fencers',
            activePistes: 'Active Pistes',
            syncStatus: 'Sync Status',
            realtime: 'Realtime'
        },
        eventSection: 'Events',
        filterAll: 'All',
        filterIndividual: 'Individual',
        filterTeam: 'Team',
        noEvents: 'No events yet, click the top right button to create your first event',
        breadcrumb: {
            home: 'Home',
            tournamentList: 'Tournament List',
            currentTournament: 'Current Tournament'
        }
    },
    eventDrawer: {
        title: 'Create Event',
        form: {
            eventName: 'Event Name',
            eventType: 'Weapon Type',
            rule: 'Rule',
            eventNature: 'Event Type',
            startTime: 'Scheduled Start Time',
            individual: 'Individual',
            team: 'Team'
        },
        placeholder: {
            eventName: 'e.g., U14 Men\'s Epee Individual',
            eventType: 'Select Weapon Type',
            rule: 'Select Rule',
            startTime: 'Select Time'
        },
        alert: {
            title: 'Note',
            description: 'After creating the event, you will proceed to fencer registration and pool arrangement.'
        },
        messages: {
            eventNameRequired: 'Please enter event name',
            eventTypeRequired: 'Please select weapon type',
            ruleRequired: 'Please select rule',
            createSuccess: 'Event created successfully'
        },
        actions: {
            cancel: 'Cancel',
            confirmCreate: 'Confirm Create'
        }
    },
    form: {
        name: 'Tournament Name',
        organizer: 'Organizer',
        location: 'Location',
        date: 'Date',
        rangeSeparator: 'to',
        startPlaceholder: 'Start date',
        endPlaceholder: 'End date',
        rule: 'Rule',
        placeholder: {
            name: 'Enter tournament name',
            organizer: 'Enter organizer name',
            location: 'Enter location'
        }
    },
    messages: {
        nameRequired: 'Tournament name is required',
        dateRequired: 'Please select a date',
        createSuccess: 'Tournament created successfully',
        createFailed: 'Failed to create, please try again'
    },
    actions: {
        cancel: 'Cancel',
        createAndEnter: 'Create & Enter'
    }
}