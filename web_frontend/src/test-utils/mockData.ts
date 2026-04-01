/**
 * Mock data factories for frontend tests
 * Uses @faker-js/faker to generate realistic test data
 */

import { faker } from '@faker-js/faker'
import type { Tournament, Stage } from '../types/tournament'
import type { User, UserRole, LoginCredentials, AuthResponse } from '../types/user'
import type {
  PendingOperation,
  SyncQueueEntry,
  ConflictItem,
  NetworkStatus,
  ClusterNode,
  ClusterStatus,
} from '../types/cluster'

export function createMockTournament(overrides: Partial<Tournament> = {}): Tournament {
  const startDate = faker.date.future()
  const endDate = faker.date.soon({ refDate: startDate })
  
  return {
    id: faker.string.uuid(),
    tournament_name: faker.company.name(),
    organizer: faker.company.name(),
    location: faker.location.city(),
    start_date: startDate.toISOString().split('T')[0],
    end_date: endDate.toISOString().split('T')[0],
    status: faker.helpers.arrayElement(['draft', 'active', 'completed']),
    is_synced: faker.datatype.boolean(),
    updated_at: faker.date.recent().getTime(),
    ...overrides,
  }
}

export function createMockStage(overrides: Partial<Stage> = {}): Stage {
  return {
    id: faker.string.uuid(),
    name: faker.hacker.noun(),
    type: faker.helpers.arrayElement(['pool', 'de']),
    config: {
      byes: faker.number.int({ min: 0, max: 8 }),
      hits: faker.number.int({ min: 5, max: 15 }),
      elimination_rate: faker.number.float({ min: 0.5, max: 0.75 }),
      final_stage: faker.hacker.verb(),
      rank_to: faker.number.int({ min: 8, max: 64 }),
    },
    ...overrides,
  }
}

export function createMockUser(overrides: Partial<User> = {}): User {
  return {
    id: faker.string.uuid(),
    username: faker.internet.username(),
    email: faker.internet.email(),
    role: faker.helpers.arrayElement<UserRole>(['ADMIN', 'SCHEDULER']),
    firstName: faker.person.firstName(),
    lastName: faker.person.lastName(),
    ...overrides,
  }
}

export function createMockLoginCredentials(
  overrides: Partial<LoginCredentials> = {}
): LoginCredentials {
  return {
    username: faker.internet.username(),
    password: faker.internet.password({ length: 12 }),
    ...overrides,
  }
}

export function createMockAuthResponse(
  overrides: Partial<AuthResponse> = {}
): AuthResponse {
  return {
    user: createMockUser(),
    error: undefined,
    ...overrides,
  }
}

export function createMockPendingOperation(
  overrides: Partial<PendingOperation> = {}
): PendingOperation {
  return {
    id: faker.string.uuid(),
    operation: faker.helpers.arrayElement(['INSERT', 'UPDATE', 'DELETE']),
    table: faker.helpers.arrayElement(['Tournament', 'Fencer', 'Event', 'Pool', 'Match']),
    data: {},
    version: faker.number.int({ min: 1, max: 100 }),
    retries: faker.number.int({ min: 0, max: 3 }),
    lastAttempt: faker.date.recent(),
    createdAt: faker.date.recent(),
    ...overrides,
  }
}

export function createMockSyncQueueEntry(
  overrides: Partial<SyncQueueEntry> = {}
): SyncQueueEntry {
  return {
    id: faker.string.uuid(),
    operations: [
      createMockPendingOperation(),
      createMockPendingOperation(),
    ],
    status: faker.helpers.arrayElement(['pending', 'processing', 'completed', 'failed']),
    createdAt: faker.date.recent(),
    updatedAt: faker.date.recent(),
    ...overrides,
  }
}

export function createMockConflictItem(overrides: Partial<ConflictItem> = {}): ConflictItem {
  return {
    id: faker.string.uuid(),
    table: faker.helpers.arrayElement(['Tournament', 'Fencer', 'Event', 'Pool', 'Match']),
    recordId: faker.string.uuid(),
    localData: { name: faker.company.name() },
    remoteData: { name: faker.company.name() },
    localVersion: faker.number.int({ min: 1, max: 10 }),
    remoteVersion: faker.number.int({ min: 1, max: 10 }),
    conflictType: faker.helpers.arrayElement([
      'version_mismatch',
      'deleted_locally',
      'deleted_remotely',
    ]),
    createdAt: faker.date.recent(),
    ...overrides,
  }
}

export function createMockNetworkStatus(
  overrides: Partial<NetworkStatus> = {}
): NetworkStatus {
  return {
    isOnline: faker.datatype.boolean(),
    lastOnline: faker.date.recent(),
    lastOffline: faker.date.recent(),
    latency: faker.number.int({ min: 10, max: 500 }),
    ...overrides,
  }
}

export function createMockClusterNode(overrides: Partial<ClusterNode> = {}): ClusterNode {
  return {
    nodeId: faker.string.uuid(),
    role: faker.helpers.arrayElement(['master', 'follower', 'single']),
    ipAddress: faker.internet.ipv4(),
    port: faker.number.int({ min: 3000, max: 9999 }),
    lastHeartbeat: faker.date.recent(),
    isHealthy: faker.datatype.boolean(),
    lastSyncId: faker.number.int({ min: 0, max: 10000 }),
    ...overrides,
  }
}

export function createMockClusterStatus(
  overrides: Partial<ClusterStatus> = {}
): ClusterStatus {
  return {
    mode: faker.helpers.arrayElement(['single', 'cluster']),
    isMaster: faker.datatype.boolean(),
    nodeId: faker.string.uuid(),
    masterUrl: faker.internet.url(),
    syncLag: faker.number.int({ min: 0, max: 100 }),
    pendingAcks: faker.number.int({ min: 0, max: 50 }),
    lastSyncTime: faker.date.recent(),
    peers: [
      createMockClusterNode(),
      createMockClusterNode(),
    ],
    ...overrides,
  }
}

export function createMockTournamentList(count: number = 5): Tournament[] {
  return Array.from({ length: count }, () => createMockTournament())
}

export function createMockUserList(count: number = 5): User[] {
  return Array.from({ length: count }, () => createMockUser())
}

export function createMockStageList(count: number = 3): Stage[] {
  return Array.from({ length: count }, () => createMockStage())
}